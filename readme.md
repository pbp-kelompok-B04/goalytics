# Tugas Kelompok PBP 04
## Anggota
- Jefferson Tirza Liman (2406435963)
- Haikal Muzaki (2406407360)
- Malik Alifan Kareem (2406348710)
- Muhammad Haikal (2406424190)
- Zakiy Nashrudin Wahid (2406496044)
- Rayyan Emir Muhammad (2406345375)

## Deskripsi Aplikasi
Proyek ini dikembangkan untuk penggemar sepak bola yang ingin mengakses dan mengelola informasi seputar pemain, pertandingan, dan diskusi sepak bola secara terorganisir dalam satu platform interaktif. Selama ini, data statistik pemain, prediksi pertandingan, serta forum diskusi tersebar di berbagai sumber yang sulit diakses secara terpusat. Melalui aplikasi ini, pengguna dapat menikmati pengalaman menyeluruh dalam mengeksplorasi dunia sepak bola modern, mulai dari menganalisis pemain, berdiskusi dengan komunitas, hingga mengelola daftar favorit pribadi.

Aplikasi ini ditujukan bagi penggemar sepak bola, analis, jurnalis olahraga, hingga pihak akademis yang membutuhkan data dan insight terkini sebagai referensi. Kebermanfaatannya terletak pada kemampuannya mengintegrasikan berbagai kebutuhan penggemar sepak bola ke dalam satu sistem yang mudah digunakan, informatif, dan interaktif.

## Daftar modul
- **Modul 1**:  Favorite player list 
    ```
    Pengguna dapat menambah, melihat, mengedit, dan menghapus daftar pemain favorit mereka. Modul ini membantu pengguna memantau performa pemain yang mereka sukai dengan cepat.
    ```

- **Modul 2**: Match prediction
    ```
    Modul ini memungkinkan pengguna membuat, membaca, memperbarui, dan menghapus prediksi pertandingan.
    ```
- **Modul 3**: Football discussion (forum-based)
    ```
    Sebuah ruang diskusi interaktif bagi pengguna untuk berbagi opini, analisis, dan berita sepak bola. Setiap postingan dan komentar dapat dikelola secara mandiri (CRUD) oleh pengguna.
    ```
- **Modul 4**: Comparison
    ```
    Comparison
    Modul ini memungkinkan pengguna membandingkan dua atau lebih pemain berdasarkan statistik utama secara visual dan interaktif. Pengguna dapat menyimpan dan mengedit hasil perbandingan mereka.
    ```
- **Modul 5**: View/edit profile
    ```
    Pengguna dapat mengelola profil pribadi mereka, termasuk preferensi liga, klub favorit, dan mode tampilan. Modul ini juga mendukung pembaruan informasi akun.
    ```
- **Modul 6**: Admin (Player database management)
    ```
    Modul khusus admin untuk mengelola database pemain. Admin dapat menambah, memperbarui, atau menghapus data pemain agar informasi di aplikasi tetap akurat dan terkini.
    ```

## Initial Dataset
- Player stats
    ```
    https://www.kaggle.com/datasets/davidcariboo/player-scores
    ```

## Role Pengguna
- Admin
    ```
    Admin adalah pengguna dengan hak akses tertinggi dalam sistem. Mereka bertanggung jawab atas pengelolaan seluruh data dan pengguna di aplikasi, termasuk pembaruan statistik, validasi konten pengguna.
    ```
- Basic User
    ```
    Basic User adalah pengguna yang sudah memiliki akun dan login ke sistem. Mereka dapat menjelajahi data, melakukan follow, membuat laporan kesalahan data,  membandingkan statistik antar pemain atau klub, serta melakukan edit/view profile
    ```
- Analyst / Data Contributor
    ```
    Analyst adalah pengguna yang memiliki sebagian akses CRUD terhadap pembaruan statistik, Role analyst hanya dapat diberikan oleh admin
    ```

## Desain Figma
https://www.figma.com/design/uMwM1qPLqnMtidT5GYAsCx/FootballHub?node-id=0-1&p=f

## Link PWS
https://jefferson-tirza-goalytics.pbp.cs.ui.ac.id
