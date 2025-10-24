from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.utils.decorators import method_decorator
from django.http import JsonResponse    
from .models import Match, Prediction, PredictionUpvote
from .forms import MatchForm, PredictionForm
from django.template.loader import render_to_string
from django.urls import reverse
from django.db import IntegrityError
from django.db.models import Count


# --- Role helpers ---
def is_admin_or_analyst(user):
    return True
    # return getattr(getattr(user, 'profile', None), 'role', None) in ['admin', 'analyst']



# --- MATCH VIEWS ---

class MatchListView(ListView):
    model = Match
    template_name = 'match_prediction/match_list.html'
    context_object_name = 'matches'
    ordering = ['-match_datetime']  # newest first, optional

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        # Check if user belongs to Admin or Analyst group
        context['can_manage_matches'] = (
            user.is_authenticated and
            is_admin_or_analyst(user) 
        )
        return context

class MatchDetailView(DetailView):
    model = Match
    template_name = 'match_prediction/match_detail.html'
    context_object_name = 'match'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        match = self.object
        
        # 1. Fetch all predictions for the match
        predictions = match.predictions.filter(is_deleted=False).select_related('user')
        
        if self.request.user.is_authenticated:
            user = self.request.user
            context['user_prediction'] = match.predictions.filter(user=user, is_deleted=False).first()
            
            # 2. CRITICAL STEP: Get a set of prediction IDs the user has upvoted
            upvoted_ids = set(
                PredictionUpvote.objects
                .filter(user=user, prediction__in=predictions)
                .values_list('prediction_id', flat=True)
            )

            # 3. Annotate the predictions with the upvoted status
            for prediction in predictions:
                # Add a new attribute that is DTL-safe
                prediction.user_has_upvoted = prediction.id in upvoted_ids
        else:
            # If not authenticated, no one has upvoted
            for prediction in predictions:
                prediction.user_has_upvoted = False

        context['predictions'] = predictions
        return context


@method_decorator(user_passes_test(lambda u: True), name='dispatch')  # allow all users for testing
class MatchCreateView(CreateView):
    model = Match
    form_class = MatchForm
    template_name = 'match_prediction/match_form.html'
    success_url = reverse_lazy('match_prediction:match_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            match = form.save()

            matches = Match.objects.all().order_by('-match_datetime')
            can_manage = is_admin_or_analyst(self.request.user)
            html = render_to_string(
                'match_prediction/partials/match_list_table.html',
                {'matches': matches, 'can_manage_matches': can_manage}
            )

            return JsonResponse({
                'message': 'Match created successfully!',
                'updateTarget': '#match-list',
                'html' : html,
            })
        messages.success(self.request, "Match created successfully!")
        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        # Handle AJAX GET: return form HTML only
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            form = self.form_class()
            return render(request, self.template_name, {'form': form})
        return super().get(request, *args, **kwargs)

@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin_or_analyst), name='dispatch')
class MatchUpdateView(UpdateView):
    model = Match
    form_class = MatchForm
    template_name = 'match_prediction/match_form.html'
    success_url = reverse_lazy('match_prediction:match_list')

    # Handle AJAX GET: return only form HTML for modal
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            form = self.form_class(instance=self.object)
            return render(request, self.template_name, {'form': form, 'object': self.object})
        return super().get(request, *args, **kwargs)

    # Handle AJAX POST: save form and return JSON
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.form_class(request.POST, instance=self.object)
        if form.is_valid():
            form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':

                matches = Match.objects.all().order_by('-match_datetime')
                can_manage = is_admin_or_analyst(self.request.user)
                html = render_to_string(
                   'match_prediction/partials/match_list_table.html',
                    {'matches': matches, 'can_manage_matches': can_manage}
                )

                return JsonResponse({
                    'status': 'success',
                    'message': 'Match updated successfully!',
                    'updateTarget': '#match-list',  # triggers reload
                    'html': html
                })
            # fallback non-AJAX
            return super().form_valid(form)
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return render(request, self.template_name, {'form': form, 'object': self.object})
            return super().form_invalid(form)


@method_decorator(user_passes_test(is_admin_or_analyst), name='dispatch')
class MatchDeleteView(DeleteView):
    model = Match
    template_name = 'match_prediction/match_confirm_delete.html'
    success_url = reverse_lazy('match_prediction:match_list')

    def post(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                self.object = self.get_object()
                match_id = self.object.id
                self.object.delete()

                return JsonResponse({
                    'status': 'success',
                    'message': 'Match deleted successfully!',
                    # This payload is expected by your ajax_handlers.js 
                    'removeTarget': f'#match-row-{match_id}' 
                })
            except Match.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Match not found.'}, status=404)
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

        # Fallback for non-AJAX POST
        return super().post(request, *args, **kwargs)



# --- PREDICTION VIEWS ---

@login_required
def add_prediction(request, match_id):
    match = get_object_or_404(Match, id=match_id, is_active=True)
    if request.method == 'POST':
        form = PredictionForm(request.POST)
        if form.is_valid():
            prediction = form.save(commit=False)
            prediction.match = match
            prediction.user = request.user
            prediction.save()
            messages.success(request, "Your prediction has been posted!")
            return redirect('match_detail', pk=match.id)
    else:
        form = PredictionForm()
    return render(request, 'match_prediction/prediction_form.html', {'form': form, 'match': match})


@login_required
def edit_prediction(request, pk):
    """Handle prediction editing via AJAX or normal page."""
    prediction = get_object_or_404(Prediction, pk=pk, is_deleted=False)
    if prediction.user != request.user and not is_admin_or_analyst(request.user):
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)

    # ---- POST: update prediction ----
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form = PredictionForm(request.POST, instance=prediction)
        if form.is_valid():
            form.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Prediction updated successfully!',
                'updateTarget': f'#prediction-{prediction.id}',  # reload just this prediction div
            })
        # return form HTML with errors if invalid
        return render(request, 'match_prediction/prediction_form.html', {
            'form': form,
            'object': prediction,
            'match': prediction.match
        }, status=400)

    # ---- GET: return form HTML ----
    if request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form = PredictionForm(instance=prediction)
        return render(request, 'match_prediction/prediction_form.html', {
            'form': form,
            'object': prediction,
            'match': prediction.match
        })

    # fallback for invalid requests
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@login_required
def delete_prediction(request, pk):
    prediction = get_object_or_404(Prediction, pk=pk, is_deleted=False)
    
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if prediction.user != request.user:
            return JsonResponse({'status': 'error', 'message': 'Permission denied.'}, status=403)
        
        prediction_id = prediction.id
        prediction.is_deleted = True
        prediction.save(update_fields=['is_deleted'])
        
        return JsonResponse({
            'status': 'success',
            'message': 'Prediction deleted successfully!',
            'removeTarget': f'#prediction-{prediction_id}' # Assuming your prediction card ID is structured like this
        })

    # Non-AJAX/GET fallback (keep redirect for compatibility if needed)
    if prediction.user != request.user:
        messages.error(request, "You are not allowed to delete this prediction.")
    else:
        prediction.is_deleted = True
        prediction.save(update_fields=['is_deleted'])
        messages.success(request, "Prediction deleted successfully!")
        
    return redirect('match_prediction:match_detail', pk=prediction.match.id)


# --- UPVOTE VIEW ---

@login_required
def toggle_upvote(request, prediction_id):
    prediction = get_object_or_404(Prediction, id=prediction_id, is_deleted=False)
    user = request.user

    upvote, created = PredictionUpvote.objects.get_or_create(prediction=prediction, user=user)
    if not created:
        upvote.delete()
        messages.info(request, "You removed your upvote.")
    else:
        messages.success(request, "You upvoted this prediction!")

    # Recalculate count for display
    prediction.recalc_upvote_count()
    return redirect('match_detail', pk=prediction.match.id)

@login_required
def ajax_add_prediction(request, match_id):
    """Handle prediction form via AJAX (GET shows form, POST submits/edits)."""
    match = get_object_or_404(Match, id=match_id, is_active=True)
    
    # 1. Check for existing prediction (UPDATE case for the current user)
    existing_prediction = Prediction.objects.filter(user=request.user, match=match, is_deleted=False).first()

    # ---- GET: return form HTML (for modal) ----
    if request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form = PredictionForm(instance=existing_prediction)
        return render(request, 'match_prediction/prediction_form.html', {
            'form': form,
            'object': existing_prediction,
            'match': match,
        })

    # ---- POST: handle submission (CREATE or UPDATE) ----
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Use existing_prediction instance if found (UPDATE), otherwise it's a new one (CREATE)
        form = PredictionForm(request.POST, instance=existing_prediction) 
        
        if form.is_valid():
            prediction = form.save(commit=False)
            prediction.match = match
            prediction.user = request.user
            
            try:
                prediction.save()
            except IntegrityError:
                # 💡 FIX FOR 500 ERROR (Problems 1 & 3): Catches the database error gracefully
                # If this is hit, the user is trying to submit a duplicate, possibly due to a race condition or model error.
                return JsonResponse({
                    'status': 'error',
                    'message': 'You already have an active prediction for this match. Please edit the existing one.',
                }, status=400) # 400 Bad Request is appropriate for client-side error
            
            # --- Auto-Refresh Logic ---
            predictions = match.predictions.filter(is_deleted=False).select_related('user')
            new_list_html = render_to_string(
                'match_prediction/partials/prediction_list.html', 
                {'predictions': predictions, 'match': match, 'request': request, 'user': request.user},
                request=request
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Prediction added/updated successfully!',
                'updateTarget': '#predictionList', 
                'html': new_list_html
            })
        
        # If invalid, return form with errors
        return render(request, 'match_prediction/prediction_form.html', {
            'form': form,
            'object': existing_prediction,
            'match': match
        }, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@login_required
def ajax_toggle_upvote(request, prediction_id):
    """
    Toggles a user's upvote status on a prediction.
    Must be called via POST and AJAX.
    """
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        prediction = get_object_or_404(Prediction, id=prediction_id, is_deleted=False)
        user = request.user
        
        # Check if the user has already upvoted this prediction
        upvote_link = PredictionUpvote.objects.filter(prediction=prediction, user=user).first()

        if upvote_link:
            # User has already upvoted: REMOVE upvote (downvote)
            upvote_link.delete()
            is_upvoted = False
        else:
            # User has not upvoted: CREATE upvote
            PredictionUpvote.objects.create(prediction=prediction, user=user)
            is_upvoted = True
        
        # Recalculate and update the cached upvote_count field
        # Use Count() for accurate and atomic calculation
        new_count = PredictionUpvote.objects.filter(prediction=prediction).count()
        prediction.upvote_count = new_count
        prediction.save(update_fields=['upvote_count'])
        
        return JsonResponse({
            'status': 'success',
            'prediction_id': prediction_id,
            'new_count': new_count,
            'is_upvoted': is_upvoted
        })

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)
