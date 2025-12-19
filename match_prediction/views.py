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
import json
from django.http import JsonResponse, HttpResponse
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from PlayerClub_Data.models import Club


# --- Role helpers ---
def is_admin_or_analyst(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if hasattr(user, 'profile'):
        try:
            # Safely access the role attribute
            return user.profile.role in ['admin', 'analyst']
        except Exception:
            # Failsafe if profile exists but role is somehow invalid/missing
            return False
            
    # Default return for any authenticated user without a profile or superuser status.
    return False



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
        match = self.get_object()
        user = self.request.user


        sort_by = self.request.GET.get('sort_by', 'newest')
        
        predictions_queryset = match.predictions.filter(is_deleted=False)
        
        if sort_by == 'upvotes':
            predictions_queryset = predictions_queryset.annotate(
                upvote_count_anno=Count('upvote_links') 
            ).order_by('-upvote_count_anno', '-created_at')
        else: 
            predictions_queryset = predictions_queryset.order_by('-created_at')
            
        # 4. Tambahkan properti dinamis (Looping diperlukan untuk user-specific data)
        user_prediction = None
        is_manager = False

        if user.is_authenticated:
            is_manager = is_admin_or_analyst(user)
            user_upvote_ids = PredictionUpvote.objects.filter(
                prediction__match=match, user=user
            ).values_list('prediction_id', flat=True)
            
            # Tambahkan properti 'user_has_upvoted' ke setiap objek Prediction 
            # yang akan digunakan di partial HTML (untuk warna tombol upvote)
            for prediction in predictions_queryset:
                prediction.user_has_upvoted = prediction.id in user_upvote_ids
                
            # Cek apakah user sudah membuat prediksi (penting untuk tombol 'Add Prediction' di HTML)
            user_prediction = predictions_queryset.filter(user=user).first()


        # 5. Tambahkan data ke context
        # Inilah variabel yang digunakan di match_detail.html dan prediction_list.html
        context['predictions'] = predictions_queryset
        context['current_sort'] = sort_by
        context['user_prediction'] = user_prediction
        context['is_manager'] = is_manager
        
        return context


@method_decorator(user_passes_test(is_admin_or_analyst), name='dispatch')  
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
                'html': html,
            })
        messages.success(self.request, "Match created successfully!")
        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            form = self.form_class()
            # ✅ Correct template for AJAX modal
            return render(request, 'match_prediction/partials/match_form_partial.html', {'form': form})
        return super().get(request, *args, **kwargs)
    
@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin_or_analyst), name='dispatch')
class MatchUpdateView(UpdateView):
    model = Match
    form_class = MatchForm
    template_name = 'match_prediction/match_form.html'
    success_url = reverse_lazy('match_prediction:match_list')

    def get(self, request, *args, **kwargs):
        """Return form partial for modal if AJAX, or full page otherwise."""
        self.object = self.get_object()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            form = self.form_class(instance=self.object)
            # ✅ Use partial template for AJAX (was the cause of 405)
            return render(request, 'match_prediction/partials/match_form_partial.html', {'form': form, 'object': self.object})
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Handle both AJAX and non-AJAX POST updates."""
        self.object = self.get_object()
        form = self.form_class(request.POST, instance=self.object)

        if form.is_valid():
            match = form.save()

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # ✅ Smart refresh target depending on where the edit was done
                referer = request.META.get('HTTP_REFERER')
                is_detail_page = referer and f'/match/{match.id}/' in referer

                if is_detail_page:
                    # Update title in match detail page
                    home_name = match.home_club.name if match.home_club else "TBD"
                    away_name = match.away_club.name if match.away_club else "TBD"
                    new_title_html = f'⚽ {home_name} <span class="mx-2 text-slate-400">vs</span> {away_name}'
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Match updated successfully!',
                        'updateTarget': '#match-title-header',
                        'html': new_title_html
                    })
                else:
                    # Update the match list in dashboard
                    matches = Match.objects.all().order_by('-match_datetime')
                    can_manage = is_admin_or_analyst(self.request.user)
                    html = render_to_string(
                        'match_prediction/partials/match_list_table.html',
                        {'matches': matches, 'can_manage_matches': can_manage}
                    )
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Match updated successfully!',
                        'updateTarget': '#match-list',
                        'html': html
                    })

            # Fallback for non-AJAX submission
            messages.success(request, "Match updated successfully!")
            return redirect(self.get_success_url())

        # Invalid form: re-render the modal with errors
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return render(
                request,
                'match_prediction/partials/match_form_partial.html',
                {'form': form, 'object': self.object},
                status=400
            )
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

    # 👇 Add this line
    return render(request, 'match_prediction/prediction_form.html', {
        'form': form,
        'match': match,
        'hide_navbar': True,  
    })


@login_required
def edit_prediction(request, pk):
    prediction = get_object_or_404(Prediction, pk=pk, is_deleted=False)
    match = prediction.match

    # GET (AJAX) → kirim HTML form ke modal
    if request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form = PredictionForm(instance=prediction)
        return render(request, 'match_prediction/partials/prediction_form_partial.html', {
            'form': form, 'object': prediction, 'match': match
        })

    # POST (AJAX) → simpan & kembalikan list terbaru
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form = PredictionForm(request.POST, instance=prediction)
        if form.is_valid():
            form.save()
            sort_by = request.GET.get('sort_by', 'newest')
            predictions = match.predictions.filter(is_deleted=False).select_related('user')

            if sort_by == 'upvotes':
                predictions = predictions.annotate(
                    upvote_count_anno=Count('upvote_links')
                ).order_by('-upvote_count_anno', '-created_at')
            else:
                predictions = predictions.order_by('-created_at')

            user_upvote_ids = PredictionUpvote.objects.filter(
                prediction__match=match, user=request.user
            ).values_list('prediction_id', flat=True)
            for p in predictions:
                p.user_has_upvoted = p.id in user_upvote_ids

            is_manager = is_admin_or_analyst(request.user)

            new_list_html = render_to_string(
                'match_prediction/partials/prediction_list.html',
                {'predictions': predictions, 'match': match, 'request': request, 'user': request.user, 'is_manager': is_manager},
                request=request
            )
            return JsonResponse({'status':'success','message':'Prediction updated successfully!','updateTarget':'#predictionList','html':new_list_html})
        return render(request, 'match_prediction/partials/prediction_form_partial.html', {'form': form, 'object': prediction, 'match': match}, status=400)

    # Fallback non-AJAX
    form = PredictionForm(instance=prediction)
    return render(request, 'match_prediction/prediction_form.html', {'form': form, 'object': prediction, 'match': match})



@login_required
def delete_prediction(request, pk):
    prediction = get_object_or_404(Prediction, pk=pk, is_deleted=False)
    
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if prediction.user != request.user and not is_admin_or_analyst(request.user):
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
    if prediction.user != request.user and not is_admin_or_analyst(request.user):
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

    prediction.recalc_upvote_count() 
    return redirect('match_prediction:match_detail', pk=prediction.match.id)

@login_required
def ajax_add_prediction(request, match_id):
    """Handle prediction form via AJAX (GET shows form, POST submits/edits)."""
    match = get_object_or_404(Match, id=match_id, is_active=True)
    
    existing_prediction = Prediction.objects.filter(user=request.user, match=match, is_deleted=False).first()


    if request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form = PredictionForm(instance=existing_prediction)
        return render(request, 'match_prediction/partials/prediction_form_partial.html', {
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
            
            sort_by = request.GET.get('sort_by', 'newest')
            
            # --- Auto-Refresh Logic ---
            predictions = match.predictions.filter(is_deleted=False).select_related('user')

            if sort_by == 'upvotes':
                predictions = predictions.annotate(
                    upvote_count_anno=Count('upvote_links')
                ).order_by('-upvote_count_anno', '-created_at')
            else:
                predictions = predictions.order_by('-created_at')

            user_upvote_ids = PredictionUpvote.objects.filter(
                prediction__match=match, user=request.user
            ).values_list('prediction_id', flat=True)

            for p in predictions:
                p.user_has_upvoted = p.id in user_upvote_ids

            is_manager = is_admin_or_analyst(request.user)

            new_list_html = render_to_string(
                'match_prediction/partials/prediction_list.html', 
                {'predictions': predictions, 'match': match, 'request': request, 'user': request.user, 'is_manager': is_manager},
                request=request
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Prediction added/updated successfully!',
                'updateTarget': '#predictionList', 
                'html': new_list_html
            })
        
        # If invalid, return form with errors
        return render(request, 'match_prediction/partials/prediction_form_partial.html', {
            'form': form,
            'object': existing_prediction,
            'match': match
        }, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@csrf_exempt
@login_required
def ajax_toggle_upvote(request, prediction_id):
    """
    Toggles a user's upvote status on a prediction.
    Must be called via POST and AJAX.
    """
    if request.method == 'POST':
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

def show_json(request):
    """Mengembalikan daftar semua Match dalam format JSON"""
    data = Match.objects.all().order_by('-match_datetime')
    return HttpResponse(serializers.serialize("json", data), content_type="application/json")

def show_predictions_json(request, match_id):
    """
    Mengembalikan daftar prediksi dengan dukungan SORTING.
    Parameter URL: ?sort_by=newest (default) atau ?sort_by=upvotes
    """
    match = get_object_or_404(Match, pk=match_id)
    
    # 1. Ambil parameter sort dari URL
    sort_by = request.GET.get('sort_by', 'newest')

    # 2. Query dasar
    predictions = match.predictions.filter(is_deleted=False).select_related('user')

    # 3. Terapkan logika sorting
    if sort_by == 'upvotes':
        predictions = predictions.annotate(
            upvote_count_anno=Count('upvote_links')
        ).order_by('-upvote_count_anno', '-created_at')
    else:
        # Default: Newest first
        predictions = predictions.order_by('-created_at')
    
    # 4. Ambil status upvote user (sama seperti sebelumnya)
    user_upvoted_ids = set()
    if request.user.is_authenticated:
        user_upvoted_ids = set(PredictionUpvote.objects.filter(
            user=request.user, 
            prediction__match=match
        ).values_list('prediction_id', flat=True))

    data = []
    for p in predictions:
        data.append({
            "model": "match_prediction.prediction",
            "pk": p.pk,
            "fields": {
                "user": p.user.id,
                "username": p.user.username,
                "match": p.match.id,
                "predicted_home_score": p.predicted_home_score,
                "predicted_away_score": p.predicted_away_score,
                "explanation": p.explanation,
                "created_at": p.created_at.isoformat(),
                "upvote_count": p.upvote_count,
                "is_deleted": p.is_deleted,
                "user_has_upvoted": p.id in user_upvoted_ids 
            }
        })
    
    return JsonResponse(data, safe=False)

@csrf_exempt
def create_prediction_flutter(request, match_id):
    """Menerima input prediksi dari Flutter (Create OR Update)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            match = get_object_or_404(Match, pk=match_id)
            
            if not request.user.is_authenticated:
                return JsonResponse({"status": "error", "message": "Authentication required"}, status=403)

            # 1. Cari prediksi yang AKTIF (is_deleted=False) milik user ini
            prediction = Prediction.objects.filter(
                user=request.user, 
                match=match, 
                is_deleted=False
            ).first()

            if prediction:
                # 2. Jika ada, UPDATE datanya
                prediction.predicted_home_score = int(data["predicted_home_score"])
                prediction.predicted_away_score = int(data["predicted_away_score"])
                prediction.explanation = data["explanation"]
                prediction.save()
                message = "Prediction updated!"
            else:
                # 3. Jika tidak ada, CREATE data baru
                Prediction.objects.create(
                    user=request.user,
                    match=match,
                    predicted_home_score=int(data["predicted_home_score"]),
                    predicted_away_score=int(data["predicted_away_score"]),
                    explanation=data["explanation"],
                    is_deleted=False
                )
                message = "Prediction created!"
            
            return JsonResponse({"status": "success", "message": message}, status=200)
        
        except Exception as e:
            # Print error di terminal agar mudah dilacak
            print(f"Error Flutter Predict: {e}") 
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
            
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=401)

# --- TAMBAHKAN FUNGSI BARU INI DI BAWAHNYA ---
def get_user_prediction_json(request, match_id):
    """Mengembalikan prediksi milik user yang sedang login untuk match tertentu"""
    if request.user.is_authenticated:
        # Cari prediksi user untuk match ini
        prediction = Prediction.objects.filter(
            user=request.user, 
            match_id=match_id, 
            is_deleted=False
        ).first()

        if prediction:
            # Return sebagai JSON list (standar serializer Django)
            return HttpResponse(serializers.serialize("json", [prediction]), content_type="application/json")
    
    # Jika tidak ada atau belum login, return 404/Empty JSON
    return JsonResponse({'status': 'not_found'}, status=404)



# ==========================================
# ADMIN / ANALYST FLUTTER API
# ==========================================

def get_user_role(request):
    """API untuk mengecek apakah user adalah admin/analyst"""
    if not request.user.is_authenticated:
        return JsonResponse({'is_manager': False, 'role': 'guest'})
    
    is_manager = is_admin_or_analyst(request.user)
    role = 'user'
    if hasattr(request.user, 'profile'):
        role = request.user.profile.role
        
    return JsonResponse({'is_manager': is_manager, 'role': role})

def get_clubs_json(request):
    """API untuk dropdown pilihan klub"""
    # Ambil semua data klub
    clubs = Club.objects.all().order_by('name')
    
    # Konversi queryset ke list of dictionaries secara manual agar lebih terkontrol
    clubs_data = []
    for club in clubs:
        clubs_data.append({
            'id': club.id,
            'name': club.name
        })
        
    # Return JSON list
    return JsonResponse(clubs_data, safe=False)

@csrf_exempt
def create_match_flutter(request):
    """API Create Match untuk Admin"""
    if request.method == 'POST':
        if not is_admin_or_analyst(request.user):
            return JsonResponse({"status": "error", "message": "Permission denied"}, status=403)
            
        try:
            data = json.loads(request.body)
            # Validasi input sederhana
            home_club = get_object_or_404(Club, pk=int(data['home_club_id']))
            away_club = get_object_or_404(Club, pk=int(data['away_club_id']))
            
            new_match = Match.objects.create(
                home_club=home_club,
                away_club=away_club,
                match_datetime=data['match_datetime'], # Pastikan format ISO String dari Flutter
                venue=data['venue'],
                created_by=request.user
            )
            new_match.save()
            return JsonResponse({"status": "success", "message": "Match created!"}, status=200)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid method"}, status=401)

@csrf_exempt
def edit_match_flutter(request, match_id):
    """API Edit Match untuk Admin"""
    if request.method == 'POST':
        if not is_admin_or_analyst(request.user):
            return JsonResponse({"status": "error", "message": "Permission denied"}, status=403)
            
        try:
            match = get_object_or_404(Match, pk=match_id)
            data = json.loads(request.body)
            
            match.home_club = get_object_or_404(Club, pk=int(data['home_club_id']))
            match.away_club = get_object_or_404(Club, pk=int(data['away_club_id']))
            match.match_datetime = data['match_datetime']
            match.venue = data['venue']
            match.save()
            
            return JsonResponse({"status": "success", "message": "Match updated!"}, status=200)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid method"}, status=401)

@csrf_exempt
def delete_match_flutter(request, match_id):
    """API Delete Match untuk Admin"""
    if request.method == 'POST':
        if not is_admin_or_analyst(request.user):
            return JsonResponse({"status": "error", "message": "Permission denied"}, status=403)
            
        try:
            match = get_object_or_404(Match, pk=match_id)
            match.delete()
            return JsonResponse({"status": "success", "message": "Match deleted!"}, status=200)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid method"}, status=401)

# --- UPDATE FUNGSI DELETE PREDICTION YANG LAMA ---
# Kita update agar Admin bisa delete punya orang lain

@csrf_exempt
def delete_prediction_flutter(request, match_id):
    """Menghapus prediksi (User sendiri OR Admin untuk user lain)"""
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({"status": "error", "message": "Login required"}, status=403)
        
        # Cek apakah ada target_user_id di body (untuk Admin menghapus punya orang)
        try:
            data = json.loads(request.body)
            target_user_id = data.get('target_user_id') # Optional
        except:
            target_user_id = None

        is_manager = is_admin_or_analyst(request.user)

        # Logika Query
        if target_user_id and is_manager:
            # Kasus Admin menghapus prediksi orang lain
            prediction = Prediction.objects.filter(
                user_id=target_user_id, 
                match_id=match_id, 
                is_deleted=False
            ).first()
        else:
            # Kasus User menghapus prediksi sendiri
            prediction = Prediction.objects.filter(
                user=request.user, 
                match_id=match_id, 
                is_deleted=False
            ).first()

        if not prediction:
            return JsonResponse({"status": "error", "message": "Prediction not found"}, status=404)

        # Lakukan Soft Delete
        prediction.is_deleted = True
        prediction.save()
        
        return JsonResponse({"status": "success", "message": "Prediction deleted"}, status=200)
    
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)