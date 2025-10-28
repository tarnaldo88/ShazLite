-- Insert songs directly into the database
-- Run this in pgAdmin Query Tool

-- Insert songs
INSERT INTO songs (title, artist, album, duration_seconds, year, genre) VALUES
('Many Men (1960s Motown Soul Almost Real AI Cover)', '50 Cent', '', 180, 2024, 'Hip Hop'),
('Notorious', 'Malaa', '', 180, 2024, 'Electronic'),
('Swing', 'SOFI TUKKER', 'SOFI TUKKER', 180, 2024, 'Electronic'),
('Black Hole Sun (1960s Motown Soul Almost Real AI Cover)', 'Soundgarden', '', 180, 2024, 'Rock');

-- Generate some mock fingerprints for each song
-- Song 1: Many Men
INSERT INTO fingerprints (song_id, hash_value, time_offset_ms, frequency_1, frequency_2, time_delta_ms) VALUES
(1, 1234567890, 1000, 440.0, 880.0, 100),
(1, 2345678901, 2000, 523.0, 1046.0, 150),
(1, 3456789012, 3000, 659.0, 1318.0, 200),
(1, 4567890123, 4000, 698.0, 1396.0, 120),
(1, 5678901234, 5000, 784.0, 1568.0, 180);

-- Song 2: Notorious  
INSERT INTO fingerprints (song_id, hash_value, time_offset_ms, frequency_1, frequency_2, time_delta_ms) VALUES
(2, 1111111111, 1000, 400.0, 800.0, 110),
(2, 2222222222, 2000, 500.0, 1000.0, 160),
(2, 3333333333, 3000, 600.0, 1200.0, 210),
(2, 4444444444, 4000, 700.0, 1400.0, 130),
(2, 5555555555, 5000, 800.0, 1600.0, 190);

-- Song 3: Swing
INSERT INTO fingerprints (song_id, hash_value, time_offset_ms, frequency_1, frequency_2, time_delta_ms) VALUES
(3, 9876543210, 1000, 450.0, 900.0, 105),
(3, 8765432109, 2000, 550.0, 1100.0, 155),
(3, 7654321098, 3000, 650.0, 1300.0, 205),
(3, 6543210987, 4000, 750.0, 1500.0, 125),
(3, 5432109876, 5000, 850.0, 1700.0, 185);

-- Song 4: Black Hole Sun
INSERT INTO fingerprints (song_id, hash_value, time_offset_ms, frequency_1, frequency_2, time_delta_ms) VALUES
(4, 1357924680, 1000, 420.0, 840.0, 115),
(4, 2468135790, 2000, 520.0, 1040.0, 165),
(4, 3579246801, 3000, 620.0, 1240.0, 215),
(4, 4680357912, 4000, 720.0, 1440.0, 135),
(4, 5791468023, 5000, 820.0, 1640.0, 195);

-- Check what was inserted
SELECT 
    s.id,
    s.title,
    s.artist,
    COUNT(f.id) as fingerprint_count
FROM songs s
LEFT JOIN fingerprints f ON s.id = f.song_id
GROUP BY s.id, s.title, s.artist
ORDER BY s.id;