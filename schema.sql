CREATE DATABASE IF NOT EXISTS hospital_db;
USE hospital_db;

CREATE TABLE IF NOT EXISTS patients (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_name VARCHAR(100) NOT NULL,
    address VARCHAR(255) NULL,
    age_band VARCHAR(10) NOT NULL,
    gender VARCHAR(10) NULL
);

CREATE TABLE IF NOT EXISTS departments (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS visits (
    visit_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    department_id INT NOT NULL,
    visit_date DATE NOT NULL,
    visit_type VARCHAR(20) NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

INSERT IGNORE INTO departments (department_name) VALUES
('General Medicine'), ('Pediatrics'), ('Orthopedics'),
('Emergency'), ('Gynecology'), ('ENT');

-- Optional synthetic sample data (run once)
INSERT INTO patients (patient_name, address, age_band, gender) VALUES
('Aarav Reddy',  'Banjara Hills, Hyderabad', '0-17',  'Male'),
('Priya Sharma', 'Madhapur, Hyderabad',      '18-29', 'Female'),
('Rahul Verma',  'Kukatpally, Hyderabad',    '30-44', 'Male'),
('Sunita Rao',   'Secunderabad',             '45-59', 'Female'),
('Venkat Naidu', 'Gachibowli, Hyderabad',    '60+',   'Male'),
('Ananya Das',   'Ameerpet, Hyderabad',      '18-29', NULL),
('Meena Iyer',   'Begumpet, Hyderabad',      '30-44', 'Female'),
('Lakshmi Devi', 'Dilsukhnagar, Hyderabad',  '60+',   'Female');

INSERT INTO visits (patient_id, department_id, visit_date, visit_type) VALUES
(1,2,'2026-08-03','Routine'), (2,5,'2026-08-10','Outpatient'),
(3,1,'2026-08-15','Follow-up'), (4,3,'2026-09-02','Outpatient'),
(5,4,'2026-09-09','Emergency'), (6,1,'2026-09-12','Routine'),
(7,5,'2026-10-01','Follow-up'), (8,6,'2026-10-05','Outpatient'),
(5,1,'2026-10-12','Follow-up'), (1,2,'2026-10-20','Emergency');
