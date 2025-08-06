DROP TABLE IF EXISTS districts;

CREATE TABLE districts (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255),
  province VARCHAR(255),
  geom GEOMETRY(MultiPolygon, 4326),
  population INTEGER,
  male_ratio FLOAT,
  female_ratio FLOAT
);

INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Ajung', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.0 -8.0, 112.1 -8.0, 112.1 -7.9, 112.0 -7.9, 112.0 -8.0))', 4326)), 133810, 0.484, 0.516);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Ambulu', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.2 -8.0, 112.3 -8.0, 112.3 -7.9, 112.2 -7.9, 112.2 -8.0))', 4326)), 147196, 0.491, 0.509);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Ambunten', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.4 -8.0, 112.5 -8.0, 112.5 -7.9, 112.4 -7.9, 112.4 -8.0))', 4326)), 79256, 0.486, 0.514);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Ampelgading', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.6 -8.0, 112.69999999999999 -8.0, 112.69999999999999 -7.9, 112.6 -7.9, 112.6 -8.0))', 4326)), 63434, 0.507, 0.493);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Arjasa', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.8 -8.0, 112.89999999999999 -8.0, 112.89999999999999 -7.9, 112.8 -7.9, 112.8 -8.0))', 4326)), 121482, 0.483, 0.517);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Arjosari', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.0 -7.8, 112.1 -7.8, 112.1 -7.7, 112.0 -7.7, 112.0 -7.8))', 4326)), 105302, 0.481, 0.519);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Arosbaya', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.2 -7.8, 112.3 -7.8, 112.3 -7.7, 112.2 -7.7, 112.2 -7.8))', 4326)), 62280, 0.489, 0.511);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Assembagus', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.4 -7.8, 112.5 -7.8, 112.5 -7.7, 112.4 -7.7, 112.4 -7.8))', 4326)), 116237, 0.504, 0.496);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Asemrowo', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.6 -7.8, 112.69999999999999 -7.8, 112.69999999999999 -7.7, 112.6 -7.7, 112.6 -7.8))', 4326)), 123563, 0.488, 0.512);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Babat', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.8 -7.8, 112.89999999999999 -7.8, 112.89999999999999 -7.7, 112.8 -7.7, 112.8 -7.8))', 4326)), 135181, 0.508, 0.492);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Badas', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.0 -7.6, 112.1 -7.6, 112.1 -7.5, 112.0 -7.5, 112.0 -7.6))', 4326)), 104987, 0.489, 0.511);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Balongbendo', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.2 -7.6, 112.3 -7.6, 112.3 -7.5, 112.2 -7.5, 112.2 -7.6))', 4326)), 127236, 0.491, 0.509);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Bangil', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.4 -7.6, 112.5 -7.6, 112.5 -7.5, 112.4 -7.5, 112.4 -7.6))', 4326)), 50851, 0.51, 0.49);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Bangililan', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.6 -7.6, 112.69999999999999 -7.6, 112.69999999999999 -7.5, 112.6 -7.5, 112.6 -7.6))', 4326)), 70926, 0.508, 0.492);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Banyuwangi', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.8 -7.6, 112.89999999999999 -7.6, 112.89999999999999 -7.5, 112.8 -7.5, 112.8 -7.6))', 4326)), 94597, 0.491, 0.509);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Baureno', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.0 -7.4, 112.1 -7.4, 112.1 -7.300000000000001, 112.0 -7.300000000000001, 112.0 -7.4))', 4326)), 78221, 0.518, 0.482);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Blimbing', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.2 -7.4, 112.3 -7.4, 112.3 -7.300000000000001, 112.2 -7.300000000000001, 112.2 -7.4))', 4326)), 94118, 0.484, 0.516);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Bluluk', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.4 -7.4, 112.5 -7.4, 112.5 -7.300000000000001, 112.4 -7.300000000000001, 112.4 -7.4))', 4326)), 99797, 0.484, 0.516);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Bondowoso', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.6 -7.4, 112.69999999999999 -7.4, 112.69999999999999 -7.300000000000001, 112.6 -7.300000000000001, 112.6 -7.4))', 4326)), 95082, 0.504, 0.496);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Bringin', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.8 -7.4, 112.89999999999999 -7.4, 112.89999999999999 -7.300000000000001, 112.8 -7.300000000000001, 112.8 -7.4))', 4326)), 55695, 0.509, 0.491);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Caleng', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.0 -7.2, 112.1 -7.2, 112.1 -7.1000000000000005, 112.0 -7.1000000000000005, 112.0 -7.2))', 4326)), 120284, 0.485, 0.515);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Curahdami', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.2 -7.2, 112.3 -7.2, 112.3 -7.1000000000000005, 112.2 -7.1000000000000005, 112.2 -7.2))', 4326)), 99615, 0.483, 0.517);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Diwek', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.4 -7.2, 112.5 -7.2, 112.5 -7.1000000000000005, 112.4 -7.1000000000000005, 112.4 -7.2))', 4326)), 88427, 0.513, 0.487);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Dander', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.6 -7.2, 112.69999999999999 -7.2, 112.69999999999999 -7.1000000000000005, 112.6 -7.1000000000000005, 112.6 -7.2))', 4326)), 131070, 0.515, 0.485);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Gedangan', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.8 -7.2, 112.89999999999999 -7.2, 112.89999999999999 -7.1000000000000005, 112.8 -7.1000000000000005, 112.8 -7.2))', 4326)), 97400, 0.503, 0.497);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Gondang', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.0 -7.0, 112.1 -7.0, 112.1 -6.9, 112.0 -6.9, 112.0 -7.0))', 4326)), 142349, 0.483, 0.517);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Gresik', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.2 -7.0, 112.3 -7.0, 112.3 -6.9, 112.2 -6.9, 112.2 -7.0))', 4326)), 136673, 0.489, 0.511);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Jombang', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.4 -7.0, 112.5 -7.0, 112.5 -6.9, 112.4 -6.9, 112.4 -7.0))', 4326)), 87930, 0.519, 0.481);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Kertosono', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.6 -7.0, 112.69999999999999 -7.0, 112.69999999999999 -6.9, 112.6 -6.9, 112.6 -7.0))', 4326)), 80512, 0.515, 0.485);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Lumajang', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.8 -7.0, 112.89999999999999 -7.0, 112.89999999999999 -6.9, 112.8 -6.9, 112.8 -7.0))', 4326)), 99823, 0.491, 0.509);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Muncar', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.0 -6.8, 112.1 -6.8, 112.1 -6.7, 112.0 -6.7, 112.0 -6.8))', 4326)), 133320, 0.513, 0.487);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Ngoro', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.2 -6.8, 112.3 -6.8, 112.3 -6.7, 112.2 -6.7, 112.2 -6.8))', 4326)), 71319, 0.495, 0.505);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Ngetos', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.4 -6.8, 112.5 -6.8, 112.5 -6.7, 112.4 -6.7, 112.4 -6.8))', 4326)), 77460, 0.507, 0.493);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Pace', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.6 -6.8, 112.69999999999999 -6.8, 112.69999999999999 -6.7, 112.6 -6.7, 112.6 -6.8))', 4326)), 141988, 0.517, 0.483);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Pacitan', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.8 -6.8, 112.89999999999999 -6.8, 112.89999999999999 -6.7, 112.8 -6.7, 112.8 -6.8))', 4326)), 134939, 0.483, 0.517);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Patianrowo', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.0 -6.6, 112.1 -6.6, 112.1 -6.5, 112.0 -6.5, 112.0 -6.6))', 4326)), 133227, 0.487, 0.513);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Perak', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.2 -6.6, 112.3 -6.6, 112.3 -6.5, 112.2 -6.5, 112.2 -6.6))', 4326)), 145568, 0.49, 0.51);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Peterongan', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.4 -6.6, 112.5 -6.6, 112.5 -6.5, 112.4 -6.5, 112.4 -6.6))', 4326)), 110589, 0.495, 0.505);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Ploso', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.6 -6.6, 112.69999999999999 -6.6, 112.69999999999999 -6.5, 112.6 -6.5, 112.6 -6.6))', 4326)), 133886, 0.508, 0.492);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Plandaan', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.8 -6.6, 112.89999999999999 -6.6, 112.89999999999999 -6.5, 112.8 -6.5, 112.8 -6.6))', 4326)), 78785, 0.507, 0.493);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Randuagung', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.0 -6.4, 112.1 -6.4, 112.1 -6.300000000000001, 112.0 -6.300000000000001, 112.0 -6.4))', 4326)), 57331, 0.489, 0.511);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Rejoso', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.2 -6.4, 112.3 -6.4, 112.3 -6.300000000000001, 112.2 -6.300000000000001, 112.2 -6.4))', 4326)), 54207, 0.512, 0.488);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Sawahan', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.4 -6.4, 112.5 -6.4, 112.5 -6.300000000000001, 112.4 -6.300000000000001, 112.4 -6.4))', 4326)), 102581, 0.491, 0.509);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Sidoarjo', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.6 -6.4, 112.69999999999999 -6.4, 112.69999999999999 -6.300000000000001, 112.6 -6.300000000000001, 112.6 -6.4))', 4326)), 77653, 0.517, 0.483);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Singosari', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.8 -6.4, 112.89999999999999 -6.4, 112.89999999999999 -6.300000000000001, 112.8 -6.300000000000001, 112.8 -6.4))', 4326)), 124341, 0.515, 0.485);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Sukorambi', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.0 -6.2, 112.1 -6.2, 112.1 -6.1000000000000005, 112.0 -6.1000000000000005, 112.0 -6.2))', 4326)), 91245, 0.489, 0.511);
INSERT INTO districts (name, province, geom, population, male_ratio, female_ratio)
VALUES ('Sukodono', 'Jawa Timur', ST_Multi(ST_GeomFromText('POLYGON((112.2 -6.2, 112.3 -6.2, 112.3 -6.1000000000000005, 112.2 -6.1000000000000005, 112.2 -6.2))', 4326)), 115435, 0.496, 0.504);