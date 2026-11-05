-- Sample data for testing ReserveIT. Safe to run once on an empty schema.
-- ALL sample accounts use the password:  ChangeMe123!   (testing only, never use in production)

INSERT INTO department (department_name) VALUES
  ('College of Computer Studies'),
  ('College of Education'),
  ('College of Business'),
  ('College of Engineering'),
  ('Facilities and Administration Office');

INSERT INTO staff (full_name, email, password_hash, role) VALUES
  ('Ana Reyes',  'admin@reserveit.test', 'pbkdf2:sha256:1000000$NipVREePC2nfDf5T$1e5d8ba7cb026ba6b1190c5d2181e36f9ef3b8423e6ad7bfb93af8d9b99c6596', 'ADMIN'),
  ('Ben Santos', 'staff@reserveit.test', 'pbkdf2:sha256:1000000$NipVREePC2nfDf5T$1e5d8ba7cb026ba6b1190c5d2181e36f9ef3b8423e6ad7bfb93af8d9b99c6596', 'STAFF');

INSERT INTO app_user (first_name, last_name, email, password_hash, role, department_id) VALUES
  ('Carla', 'Dizon', 'student@reserveit.test', 'pbkdf2:sha256:1000000$NipVREePC2nfDf5T$1e5d8ba7cb026ba6b1190c5d2181e36f9ef3b8423e6ad7bfb93af8d9b99c6596', 'STUDENT',
      (SELECT department_id FROM department WHERE department_name = 'College of Computer Studies')),
  ('Dante', 'Lopez', 'faculty@reserveit.test', 'pbkdf2:sha256:1000000$NipVREePC2nfDf5T$1e5d8ba7cb026ba6b1190c5d2181e36f9ef3b8423e6ad7bfb93af8d9b99c6596', 'FACULTY',
      (SELECT department_id FROM department WHERE department_name = 'College of Education')),
  ('Ella', 'Cruz', 'student2@reserveit.test', 'pbkdf2:sha256:1000000$NipVREePC2nfDf5T$1e5d8ba7cb026ba6b1190c5d2181e36f9ef3b8423e6ad7bfb93af8d9b99c6596', 'STUDENT',
      (SELECT department_id FROM department WHERE department_name = 'College of Business'));

INSERT INTO room (room_name, building, capacity, room_type) VALUES
  ('Room 101',          'Main Building',    40, 'CLASSROOM'),
  ('Room 102',          'Main Building',    40, 'CLASSROOM'),
  ('Room 201',          'Main Building',    35, 'CLASSROOM'),
  ('Computer Lab 1',    'Technology Hall',  30, 'LABORATORY'),
  ('Computer Lab 2',    'Technology Hall',  30, 'LABORATORY'),
  ('Conference Room A', 'Admin Building',   20, 'CONFERENCE'),
  ('Function Hall',     'Admin Building',  120, 'CONFERENCE');

INSERT INTO material (material_name, category, total_quantity, available_quantity) VALUES
  ('Projector',            'AV_EQUIPMENT', 6,  6),
  ('Extension Cord',       'SUPPLIES',     12, 12),
  ('Portable Whiteboard',  'FURNITURE',    4,  4),
  ('Sound System',         'AV_EQUIPMENT', 2,  2),
  ('Wireless Microphone',  'AV_EQUIPMENT', 5,  5),
  ('Folding Table',        'FURNITURE',    15, 15);

-- Sample reservations (dates are relative to today so the data never goes stale)
INSERT INTO reservation (user_id, room_id, staff_id, reservation_date, start_time, end_time, purpose, status) VALUES
  ((SELECT user_id FROM app_user WHERE email = 'student@reserveit.test'),
   (SELECT room_id FROM room WHERE room_name = 'Room 101'),
   (SELECT staff_id FROM staff WHERE email = 'staff@reserveit.test'),
   CURRENT_DATE + 1, '09:00', '11:00', 'Thesis consultation with panel', 'APPROVED'),
  ((SELECT user_id FROM app_user WHERE email = 'faculty@reserveit.test'),
   (SELECT room_id FROM room WHERE room_name = 'Computer Lab 1'),
   NULL,
   CURRENT_DATE + 2, '13:00', '15:00', 'Make-up class for Programming 1', 'PENDING'),
  ((SELECT user_id FROM app_user WHERE email = 'student2@reserveit.test'),
   (SELECT room_id FROM room WHERE room_name = 'Function Hall'),
   (SELECT staff_id FROM staff WHERE email = 'staff@reserveit.test'),
   CURRENT_DATE - 3, '08:00', '12:00', 'Business plan pitch day', 'COMPLETED');

INSERT INTO reservation_material (reservation_id, material_id, quantity_requested)
SELECT r.reservation_id, m.material_id, x.qty
FROM (VALUES
  ('Thesis consultation with panel',  'Projector',           1),
  ('Thesis consultation with panel',  'Extension Cord',      2),
  ('Make-up class for Programming 1', 'Projector',           1),
  ('Business plan pitch day',         'Sound System',        1),
  ('Business plan pitch day',         'Wireless Microphone', 2)
) AS x(purpose, material_name, qty)
JOIN reservation r ON r.purpose = x.purpose
JOIN material m ON m.material_name = x.material_name;

-- Approved reservations are holding stock: reduce what is currently available
UPDATE material m
SET available_quantity = m.total_quantity - held.qty
FROM (
  SELECT rm.material_id, SUM(rm.quantity_requested)::int AS qty
  FROM reservation_material rm
  JOIN reservation r ON r.reservation_id = rm.reservation_id
  WHERE r.status = 'APPROVED'
  GROUP BY rm.material_id
) AS held
WHERE held.material_id = m.material_id;

-- One unpaid sample penalty
INSERT INTO penalty (reservation_id, reason, amount)
SELECT reservation_id, 'LATE_RETURN', 150.00
FROM reservation WHERE purpose = 'Business plan pitch day';
