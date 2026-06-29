/*
seed_2020.sql
Populate the entire schemafinal.sql with a 2020-flavored baseline + extra randomized data.

Design goals:
- Re-runnable: uses ON CONFLICT DO NOTHING where practical.
- FK-safe: inserts core reference tables first.
- Deterministic-ish randomness: uses setseed().
*/

BEGIN;
SELECT setseed(0.2020);

/* 1) Reference / foundational tables */
INSERT INTO Currency (currency_id, currency_name, exchange_rate, is_gold_standard) VALUES
  (1, 'US Dollar', 1.000000, FALSE),
  (2, 'Euro', 0.820000, FALSE),
  (3, 'Chinese Yuan', 6.900000, FALSE),
  (4, 'Japanese Yen', 106.000000, FALSE),
  (5, 'British Pound', 0.730000, FALSE),
  (6, 'Indian Rupee', 74.100000, FALSE),
  (7, 'Russian Ruble', 73.500000, FALSE),
  (8, 'Brazilian Real', 5.200000, FALSE),
  (9, 'Canadian Dollar', 1.340000, FALSE),
  (10, 'Swiss Franc', 0.910000, FALSE)
ON CONFLICT (currency_id) DO NOTHING;

INSERT INTO GovernmentType (government_type_id, government_name, social_policy, economic_policy, diplomatic_policy) VALUES
  (1, 'Federal Republic', 5, 8, 5),
  (2, 'Single-Party State', 2, 6, 3),
  (3, 'Constitutional Monarchy', 7, 7, 6),
  (4, 'Parliamentary Democracy', 6, 7, 6),
  (5, 'Military Junta', 1, 4, 2),
  (6, 'Absolute Monarchy', 2, 5, 4)
ON CONFLICT (government_type_id) DO NOTHING;

INSERT INTO Ideology (ideology_id, ideology_name, base_consumption_modifier, max_tariff_limit, can_join_foreign_spheres, allows_free_trade) VALUES
  (1, 'Liberal', 1.05, 0.60, TRUE, TRUE),
  (2, 'Conservative', 1.00, 0.80, TRUE, TRUE),
  (3, 'Socialist', 1.10, 0.70, TRUE, FALSE),
  (4, 'Authoritarian', 0.95, 1.00, FALSE, FALSE),
  (5, 'Libertarian', 1.08, 0.40, TRUE, TRUE),
  (6, 'Nationalist', 0.98, 1.00, TRUE, FALSE)
ON CONFLICT (ideology_id) DO NOTHING;

INSERT INTO Goods (goods_id, good_name, good_type) VALUES
  (1, 'Grain', 'Food'),
  (2, 'Fish', 'Food'),
  (3, 'Coal', 'Raw'),
  (4, 'Iron', 'Raw'),
  (5, 'Oil', 'Raw'),
  (6, 'Timber', 'Raw'),
  (7, 'Steel', 'Industrial'),
  (8, 'Tools', 'Industrial'),
  (9, 'Textiles', 'Consumer'),
  (10, 'Clothes', 'Consumer'),
  (11, 'Furniture', 'Consumer'),
  (12, 'Cement', 'Industrial'),
  (13, 'Chemicals', 'Industrial'),
  (14, 'Electronics', 'Consumer'),
  (15, 'Cars', 'Consumer'),
  (16, 'Arms', 'Military'),
  (17, 'Ammunition', 'Military'),
  (18, 'Medicine', 'Consumer'),
  (19, 'Coffee', 'Food'),
  (20, 'Rubber', 'Raw')
ON CONFLICT (goods_id) DO NOTHING;

-- Add additional random goods up to 60 total
WITH base AS (SELECT COALESCE(MAX(goods_id), 0) AS mx FROM Goods)
INSERT INTO Goods (goods_id, good_name, good_type)
SELECT (SELECT mx FROM base) + g.i,
       'Good-' || ((SELECT mx FROM base) + g.i),
       (ARRAY['Food','Raw','Industrial','Consumer','Military'])[1 + floor(random()*5)]
FROM generate_series(1, GREATEST(0, 60 - (SELECT COUNT(*) FROM Goods))) AS g(i)
ON CONFLICT (goods_id) DO NOTHING;

INSERT INTO PopulationTypes (pop_id, pop_name, is_taxable) VALUES
  (1, 'Farmers', TRUE),
  (2, 'Laborers', TRUE),
  (3, 'Clerks', TRUE),
  (4, 'Craftsmen', TRUE),
  (5, 'Engineers', TRUE),
  (6, 'Bureaucrats', TRUE),
  (7, 'Officers', TRUE),
  (8, 'Soldiers', TRUE),
  (9, 'Aristocrats', TRUE),
  (10, 'Capitalists', TRUE)
ON CONFLICT (pop_id) DO NOTHING;

/* 2) Countries (baseline + randomized extras) */
INSERT INTO Country (country_id, country_name, gdp, national_debt, government_type_id, currency_id) VALUES
  (1, 'United States', 21060000000000.00, 27740000000000.00, 1, 1),
  (2, 'China', 14720000000000.00, 10100000000000.00, 2, 3),
  (3, 'Japan', 5050000000000.00, 12200000000000.00, 3, 4),
  (4, 'Germany', 3850000000000.00, 2700000000000.00, 4, 2),
  (5, 'United Kingdom', 2760000000000.00, 2800000000000.00, 3, 5),
  (6, 'India', 2660000000000.00, 2200000000000.00, 4, 6),
  (7, 'Russia', 1480000000000.00, 300000000000.00, 6, 7),
  (8, 'Brazil', 1440000000000.00, 1700000000000.00, 4, 8),
  (9, 'Canada', 1640000000000.00, 1100000000000.00, 4, 9),
  (10, 'Switzerland', 715000000000.00, 250000000000.00, 4, 10)
ON CONFLICT (country_id) DO NOTHING;

-- Add more countries up to 40
WITH base AS (SELECT COALESCE(MAX(country_id), 0) AS mx FROM Country),
need AS (SELECT GREATEST(0, 40 - (SELECT COUNT(*) FROM Country)) AS n)
INSERT INTO Country (country_id, country_name, gdp, national_debt, government_type_id, currency_id)
SELECT (SELECT mx FROM base) + i,
       'Country-' || ((SELECT mx FROM base) + i),
       round((5e10 + random()*6e12)::numeric, 2),
       round((1e10 + random()*8e12)::numeric, 2),
       (SELECT government_type_id FROM GovernmentType ORDER BY random() LIMIT 1),
       (SELECT currency_id FROM Currency ORDER BY random() LIMIT 1)
FROM generate_series(1, (SELECT n FROM need)) AS s(i)
ON CONFLICT (country_id) DO NOTHING;

/* 3) Geography: MapNode (if you already generated 3000 nodes, this adds none) */
-- Ensure at least 200 nodes exist for demo purposes
WITH cur AS (SELECT COUNT(*) AS c FROM MapNode),
base AS (SELECT COALESCE(MAX(node_id), 0) AS mx FROM MapNode),
need AS (SELECT GREATEST(0, 200 - (SELECT c FROM cur)) AS n)
INSERT INTO MapNode (node_id, node_name, terrain_type, is_sea_zone)
SELECT (SELECT mx FROM base) + i,
       'SeedNode-' || ((SELECT mx FROM base) + i),
       (ARRAY['Plains','Forest','Hills','Mountain','Urban','Desert','Sea'])[1 + floor(random()*7)],
       (random() < 0.18)
FROM generate_series(1, (SELECT n FROM need)) AS s(i)
ON CONFLICT (node_id) DO NOTHING;

/* 4) Provinces: one per node, but only add if Province is empty */
WITH has AS (SELECT COUNT(*) AS c FROM Province)
INSERT INTO Province (province_id, node_id, owner_country_id, controller_country_id)
SELECT row_number() OVER () + (SELECT COALESCE(MAX(province_id), 0) FROM Province) AS province_id,
       mn.node_id,
       c.country_id,
       c.country_id
FROM MapNode mn
JOIN LATERAL (SELECT country_id FROM Country ORDER BY random() LIMIT 1) c ON TRUE
WHERE (SELECT c FROM has) = 0
ON CONFLICT (province_id) DO NOTHING;

/* 5) ProvincePopulation */
WITH base AS (SELECT COALESCE(MAX(province_pop_id), 0) AS mx FROM ProvincePopulation)
INSERT INTO ProvincePopulation (province_pop_id, province_id, pop_type_id, headcount, wealth, militancy)
SELECT (SELECT mx FROM base) + row_number() OVER () AS province_pop_id,
       p.province_id,
       pt.pop_id,
       (50000 + floor(random()*900000))::bigint,
       round((random()*50000)::numeric, 2),
       round((random()*35)::numeric, 2)
FROM Province p
JOIN PopulationTypes pt ON TRUE
WHERE NOT EXISTS (
  SELECT 1 FROM ProvincePopulation pp
  WHERE pp.province_id = p.province_id AND pp.pop_type_id = pt.pop_id
)
-- keep it reasonable: only seed a subset of pop types per province
AND random() < 0.35;

/* 6) CountryStockpile */
INSERT INTO CountryStockpile (country_id, goods_id, amount)
SELECT c.country_id, g.goods_id, (floor(random()*500000))::bigint
FROM Country c
JOIN Goods g ON TRUE
WHERE random() < 0.18
ON CONFLICT (country_id, goods_id) DO NOTHING;

/* 7) FactoryType */
INSERT INTO FactoryType (factory_type_id, factory_name, consumed_goods_id, produced_goods_id)
SELECT ft.factory_type_id,
       ft.factory_name,
       ft.consumed_goods_id,
       ft.produced_goods_id
FROM (VALUES
  (1, 'Steel Mill', 4, 7),
  (2, 'Tool Workshop', 7, 8),
  (3, 'Textile Mill', 6, 9),
  (4, 'Clothing Factory', 9, 10),
  (5, 'Furniture Factory', 6, 11),
  (6, 'Cement Plant', 4, 12),
  (7, 'Chemical Plant', 3, 13),
  (8, 'Electronics Plant', 13, 14),
  (9, 'Automobile Plant', 7, 15),
  (10, 'Arms Factory', 7, 16),
  (11, 'Ammo Factory', 3, 17),
  (12, 'Pharmaceuticals', 13, 18)
) AS ft(factory_type_id, factory_name, consumed_goods_id, produced_goods_id)
ON CONFLICT (factory_type_id) DO NOTHING;

/* 8) ProvinceFactory */
WITH base AS (SELECT COALESCE(MAX(factory_instance_id), 0) AS mx FROM ProvinceFactory)
INSERT INTO ProvinceFactory (factory_instance_id, province_id, factory_type_id, is_active)
SELECT (SELECT mx FROM base) + row_number() OVER () AS factory_instance_id,
       p.province_id,
       (SELECT factory_type_id FROM FactoryType ORDER BY random() LIMIT 1),
       (random() < 0.85)
FROM Province p
WHERE random() < 0.30;

/* 9) MarketSphere + Members */
INSERT INTO MarketSphere (sphere_id, leader_country_id, sphere_name, internal_tariff_rate)
SELECT s.sphere_id,
       s.leader_country_id,
       s.sphere_name,
       s.internal_tariff_rate
FROM (VALUES
  (1, 1, 'Atlantic Trade Bloc', 0.03),
  (2, 2, 'Pan-Asian Sphere', 0.05),
  (3, 4, 'Continental Market', 0.02)
) AS s(sphere_id, leader_country_id, sphere_name, internal_tariff_rate)
ON CONFLICT (sphere_id) DO NOTHING;

INSERT INTO MarketSphereMembers (sphere_id, country_id, joined_tick)
SELECT ms.sphere_id, c.country_id, (100 + floor(random()*2000))::int
FROM MarketSphere ms
JOIN Country c ON TRUE
WHERE random() < 0.20
ON CONFLICT (sphere_id, country_id) DO NOTHING;

/* 10) TradePolicy */
WITH pairs AS (
  SELECT c1.country_id AS a, c2.country_id AS b
  FROM Country c1
  JOIN Country c2 ON c1.country_id <> c2.country_id
  WHERE random() < 0.04
)
INSERT INTO TradePolicy (policy_id, country_id, target_country_id, is_embargoed, tariff_rate)
SELECT (SELECT COALESCE(MAX(policy_id), 0) FROM TradePolicy) + row_number() OVER () AS policy_id,
       a, b,
       (random() < 0.06),
       round((random()*0.25)::numeric, 2)
FROM pairs
ON CONFLICT (policy_id) DO NOTHING;

/* 11) MarketOrders */
WITH base AS (SELECT COALESCE(MAX(order_id), 0) AS mx FROM MarketOrders)
INSERT INTO MarketOrders (order_id, country_id, goods_id, is_buy_order, quantity, fulfilled_quantity, tick_submitted)
SELECT (SELECT mx FROM base) + row_number() OVER () AS order_id,
       c.country_id,
       g.goods_id,
       (random() < 0.55),
       (1000 + floor(random()*200000))::bigint,
       0,
       (1000 + floor(random()*3000))::int
FROM Country c
JOIN LATERAL (SELECT goods_id FROM Goods ORDER BY random() LIMIT 1) g ON TRUE
WHERE random() < 0.70;

/* 12) ActiveTradeRoute */
WITH base AS (SELECT COALESCE(MAX(route_id), 0) AS mx FROM ActiveTradeRoute),
pairs AS (
  SELECT c1.country_id AS buyer, c2.country_id AS seller
  FROM Country c1
  JOIN Country c2 ON c1.country_id <> c2.country_id
  WHERE random() < 0.03
)
INSERT INTO ActiveTradeRoute (route_id, buyer_country_id, seller_country_id, goods_id, quantity, route_efficiency, tick_established)
SELECT (SELECT mx FROM base) + row_number() OVER () AS route_id,
       buyer,
       seller,
       (SELECT goods_id FROM Goods ORDER BY random() LIMIT 1),
       (1000 + floor(random()*400000))::bigint,
       round((0.60 + random()*0.45)::numeric, 2),
       (900 + floor(random()*4000))::int
FROM pairs;

/* 13) Leaders */
WITH base AS (SELECT COALESCE(MAX(leader_id), 0) AS mx FROM CountryCivLeaders)
INSERT INTO CountryCivLeaders (leader_id, country_id, leader_name, administration, economy, diplomacy, ideology_id)
SELECT (SELECT mx FROM base) + row_number() OVER () AS leader_id,
       c.country_id,
       'CivLeader-' || c.country_id,
       floor(random()*10)::int,
       floor(random()*10)::int,
       floor(random()*10)::int,
       (SELECT ideology_id FROM Ideology ORDER BY random() LIMIT 1)
FROM Country c
WHERE NOT EXISTS (SELECT 1 FROM CountryCivLeaders x WHERE x.country_id = c.country_id);

WITH base AS (SELECT COALESCE(MAX(leader_id), 0) AS mx FROM CountryMilLeaders)
INSERT INTO CountryMilLeaders (leader_id, country_id, leader_name, attack, defence, manoeuvre, logistics)
SELECT (SELECT mx FROM base) + row_number() OVER () AS leader_id,
       c.country_id,
       'MilLeader-' || c.country_id,
       floor(random()*10)::int,
       floor(random()*10)::int,
       floor(random()*10)::int,
       floor(random()*10)::int
FROM Country c
WHERE NOT EXISTS (SELECT 1 FROM CountryMilLeaders x WHERE x.country_id = c.country_id);

/* 14) Military */
INSERT INTO CountryMilitary (country_id, manpower, cavalry, infantry, artillery, light_ships, heavy_ships, submarines, transport_ships)
SELECT c.country_id,
       (100000 + floor(random()*5000000))::bigint,
       floor(random()*8000)::int,
       floor(random()*120000)::int,
       floor(random()*12000)::int,
       floor(random()*250)::int,
       floor(random()*120)::int,
       floor(random()*90)::int,
       floor(random()*220)::int
FROM Country c
ON CONFLICT (country_id) DO NOTHING;

/* 15) Diplomacy */
WITH pairs AS (
  SELECT c1.country_id AS a, c2.country_id AS b
  FROM Country c1
  JOIN Country c2 ON c1.country_id < c2.country_id
  WHERE random() < 0.12
)
INSERT INTO DiplomaticRelations (country_id_1, country_id_2, relation_value, has_alliance, has_non_aggression_pact)
SELECT a, b,
       (floor(random()*401) - 200)::int,
       (random() < 0.08),
       (random() < 0.14)
FROM pairs
ON CONFLICT (country_id_1, country_id_2) DO NOTHING;

/* 16) War + Participants */
WITH base AS (SELECT COALESCE(MAX(war_id), 0) AS mx FROM War)
INSERT INTO War (war_id, war_name, war_progress, start_tick)
SELECT (SELECT mx FROM base) + i AS war_id,
       'SeedWar-' || ((SELECT mx FROM base) + i),
       floor(random()*101)::int,
       (500 + floor(random()*5000))::int
FROM generate_series(1, 5) s(i)
ON CONFLICT (war_id) DO NOTHING;

-- Each war has a few participants
INSERT INTO WarParticipants (war_id, country_id, is_attacker)
SELECT w.war_id,
       c.country_id,
       (random() < 0.5)
FROM War w
JOIN LATERAL (
  SELECT country_id FROM Country ORDER BY random() LIMIT (2 + floor(random()*5))::int
) c ON TRUE
ON CONFLICT (war_id, country_id) DO NOTHING;

/* 17) PopConsumptionNeed */
INSERT INTO PopConsumptionNeed (pop_type_id, goods_id, amount_per_100k)
SELECT pt.pop_id,
       g.goods_id,
       round((0.1 + random()*15.0)::numeric, 4)
FROM PopulationTypes pt
JOIN Goods g ON TRUE
WHERE random() < 0.20
ON CONFLICT (pop_type_id, goods_id) DO NOTHING;

COMMIT;