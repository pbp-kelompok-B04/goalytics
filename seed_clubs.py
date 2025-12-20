import os
import django
import json

# 1. Setup Django Environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "goalytics.settings")
django.setup()

from PlayerClub_Data.models import Club

def seed_clubs():
    print("Mulai membaca data Klub...")
    
    # Path ke file JSON
    json_file_path = os.path.join('PlayerClub_Data', 'data', 'club_stats.json')
    
    if not os.path.exists(json_file_path):
        print(f"ERROR: File tidak ditemukan di {json_file_path}")
        return

    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            clubs_data = json.load(f) # Ini akan me-load List of Dictionaries
            
        print(f"Total data mentah ditemukan: {len(clubs_data)} baris.")
        
        count_created = 0
        count_updated = 0
        
        for item in clubs_data:
            # KOREKSI PENTING: JSON menggunakan key 'team', bukan 'name'
            if 'team' in item:
                club_name = item['team']
                
                # Kita gunakan update_or_create untuk mengisi field lain juga (league, season, dll)
                obj, created = Club.objects.update_or_create(
                    name=club_name, # Field unik untuk pencarian
                    defaults={
                        'league': item.get('league', 'Unknown'),
                        'season': item.get('season', '2425'),
                        # Masukkan stats lain jika model mendukungnya
                        'total_goal': item.get('gls', 0),
                        'total_assist': item.get('ast', 0),
                        'expected_xg': item.get('xg', 0.0),
                        'expected_xag': item.get('xag', 0.0),
                    }
                )
                
                if created:
                    count_created += 1
                else:
                    count_updated += 1
            else:
                print(f"Warning: Item tanpa key 'team' ditemukan: {item}")
        
        print("-" * 30)
        print(f"PROSES SELESAI!")
        print(f"Klub Baru Ditambahkan : {count_created}")
        print(f"Klub Lama Diupdate    : {count_updated}")
        print(f"Total Klub di Database: {Club.objects.count()}")
        print("-" * 30)
        
    except Exception as e:
        print(f"Terjadi kesalahan fatal: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    seed_clubs()