/* 1. Core Definitions */
CREATE TABLE Currency (
    currency_id INT PRIMARY KEY,
    currency_name VARCHAR(50) UNIQUE NOT NULL,
    exchange_rate DECIMAL(15,6) NOT NULL,
    is_gold_standard BOOLEAN DEFAULT FALSE
);

CREATE TABLE Ideology (
    ideology_id INT PRIMARY KEY,
    ideology_name VARCHAR(50) UNIQUE NOT NULL,
    base_consumption_modifier DECIMAL(5,2) DEFAULT 1.00,
    max_tariff_limit DECIMAL(5,2) DEFAULT 1.00, 
    can_join_foreign_spheres BOOLEAN DEFAULT TRUE,
    allows_free_trade BOOLEAN DEFAULT TRUE
);

CREATE TABLE GovernmentType (
    government_type_id INT PRIMARY KEY,
    government_name VARCHAR(50) UNIQUE NOT NULL,
    social_policy INT DEFAULT 0,
    economic_policy INT DEFAULT 0,
    diplomatic_policy INT DEFAULT 0
);

CREATE TABLE Goods (
    goods_id INT PRIMARY KEY,
    good_name VARCHAR(30) UNIQUE NOT NULL,
    good_type VARCHAR(30) NOT NULL /* Removed UNIQUE constraint here so multiple goods can be "Food" */
);

CREATE TABLE PopulationTypes (
    pop_id INT PRIMARY KEY,
    pop_name VARCHAR(80) UNIQUE NOT NULL,
    is_taxable BOOLEAN DEFAULT TRUE
);

/* 2. State and Geography */
CREATE TABLE Country (
    country_id INT PRIMARY KEY,
    country_name VARCHAR(80) UNIQUE NOT NULL,
    gdp DECIMAL(30,2) DEFAULT 0.00,
    national_debt DECIMAL(30,2) DEFAULT 0.00,
    government_type_id INT,
    currency_id INT,
    FOREIGN KEY (government_type_id) REFERENCES GovernmentType(government_type_id),
    FOREIGN KEY (currency_id) REFERENCES Currency(currency_id)
);

CREATE TABLE MapNode (
    node_id INT PRIMARY KEY,
    node_name VARCHAR(100) NOT NULL,
    terrain_type VARCHAR(50) NOT NULL,
    is_sea_zone BOOLEAN DEFAULT FALSE
);

CREATE TABLE PrecalculatedPath (
    node_a_id INT,
    node_b_id INT,
    total_distance DECIMAL(10,2) NOT NULL,
    requires_sea_transport BOOLEAN NOT NULL,
    PRIMARY KEY (node_a_id, node_b_id),
    FOREIGN KEY (node_a_id) REFERENCES MapNode(node_id),
    FOREIGN KEY (node_b_id) REFERENCES MapNode(node_id)
);

CREATE TABLE Province (
    province_id INT PRIMARY KEY,
    node_id INT UNIQUE NOT NULL,
    owner_country_id INT NOT NULL,
    controller_country_id INT NOT NULL,
    FOREIGN KEY (node_id) REFERENCES MapNode(node_id),
    FOREIGN KEY (owner_country_id) REFERENCES Country(country_id),
    FOREIGN KEY (controller_country_id) REFERENCES Country(country_id)
);

/* 3. Provincial Economy and Demographics */
CREATE TABLE ProvincePopulation (
    province_pop_id INT PRIMARY KEY,
    province_id INT NOT NULL,
    pop_type_id INT,
    headcount BIGINT NOT NULL CHECK (headcount >= 0),
    wealth DECIMAL(15,2) DEFAULT 0.00,
    militancy DECIMAL(5,2) DEFAULT 0.00 CHECK (militancy BETWEEN 0 AND 100),
    FOREIGN KEY (province_id) REFERENCES Province(province_id),
    FOREIGN KEY (pop_type_id) REFERENCES PopulationTypes(pop_id)
);

CREATE TABLE CountryStockpile (
    country_id INT,
    goods_id INT,
    amount BIGINT DEFAULT 0 CHECK (amount >= 0),
    PRIMARY KEY (country_id, goods_id),
    FOREIGN KEY (country_id) REFERENCES Country(country_id),
    FOREIGN KEY (goods_id) REFERENCES Goods(goods_id)
);

CREATE TABLE FactoryType (
    factory_type_id INT PRIMARY KEY,
    factory_name VARCHAR(50) NOT NULL,
    consumed_goods_id INT,
    produced_goods_id INT,
    FOREIGN KEY (consumed_goods_id) REFERENCES Goods(goods_id),
    FOREIGN KEY (produced_goods_id) REFERENCES Goods(goods_id)
);

CREATE TABLE ProvinceFactory (
    factory_instance_id INT PRIMARY KEY,
    province_id INT NOT NULL,
    factory_type_id INT,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (province_id) REFERENCES Province(province_id),
    FOREIGN KEY (factory_type_id) REFERENCES FactoryType(factory_type_id)
);

/* 4. Global Market and Trade Spheres */
CREATE TABLE MarketSphere (
    sphere_id INT PRIMARY KEY,
    leader_country_id INT,
    sphere_name VARCHAR(100) NOT NULL,
    internal_tariff_rate DECIMAL(5,2) DEFAULT 0.00,
    FOREIGN KEY (leader_country_id) REFERENCES Country(country_id)
);

CREATE TABLE MarketSphereMembers (
    sphere_id INT,
    country_id INT,
    joined_tick INT NOT NULL,
    PRIMARY KEY (sphere_id, country_id),
    FOREIGN KEY (sphere_id) REFERENCES MarketSphere(sphere_id),
    FOREIGN KEY (country_id) REFERENCES Country(country_id)
);

CREATE TABLE TradePolicy (
    policy_id INT PRIMARY KEY,
    country_id INT,
    target_country_id INT,
    is_embargoed BOOLEAN DEFAULT FALSE,
    tariff_rate DECIMAL(5,2) DEFAULT 0.00,
    FOREIGN KEY (country_id) REFERENCES Country(country_id),
    FOREIGN KEY (target_country_id) REFERENCES Country(country_id),
    CHECK (country_id != target_country_id)
);

CREATE TABLE MarketOrders (
    order_id INT PRIMARY KEY,
    country_id INT,
    goods_id INT,
    is_buy_order BOOLEAN NOT NULL,
    quantity BIGINT NOT NULL CHECK (quantity > 0),
    fulfilled_quantity BIGINT DEFAULT 0,
    tick_submitted INT NOT NULL,
    FOREIGN KEY (country_id) REFERENCES Country(country_id),
    FOREIGN KEY (goods_id) REFERENCES Goods(goods_id)
);

CREATE TABLE ActiveTradeRoute (
    route_id INT PRIMARY KEY,
    buyer_country_id INT,
    seller_country_id INT,
    goods_id INT,
    quantity BIGINT NOT NULL,
    route_efficiency DECIMAL(5,2) DEFAULT 1.00, /* Lowered by simplified blockades */
    tick_established INT NOT NULL,
    FOREIGN KEY (buyer_country_id) REFERENCES Country(country_id),
    FOREIGN KEY (seller_country_id) REFERENCES Country(country_id),
    FOREIGN KEY (goods_id) REFERENCES Goods(goods_id)
);

/* 5. Leaders, Military, and Diplomacy */
CREATE TABLE CountryCivLeaders (
    leader_id INT PRIMARY KEY,
    country_id INT,
    leader_name VARCHAR(80) NOT NULL,
    administration INT DEFAULT 0,
    economy INT DEFAULT 0,
    diplomacy INT DEFAULT 0,
    ideology_id INT,
    FOREIGN KEY (country_id) REFERENCES Country(country_id),
    FOREIGN KEY (ideology_id) REFERENCES Ideology(ideology_id)
);

CREATE TABLE CountryMilLeaders (
    leader_id INT PRIMARY KEY,
    country_id INT,
    leader_name VARCHAR(80) NOT NULL,
    attack INT DEFAULT 0,
    defence INT DEFAULT 0,
    manoeuvre INT DEFAULT 0,
    logistics INT DEFAULT 0,
    FOREIGN KEY (country_id) REFERENCES Country(country_id)
);

CREATE TABLE CountryMilitary (
    country_id INT PRIMARY KEY,
    manpower BIGINT DEFAULT 0 CHECK (manpower >= 0),
    cavalry INT DEFAULT 0,
    infantry INT DEFAULT 0,
    artillery INT DEFAULT 0,
    light_ships INT DEFAULT 0,
    heavy_ships INT DEFAULT 0,
    submarines INT DEFAULT 0,
    transport_ships INT DEFAULT 0,
    FOREIGN KEY (country_id) REFERENCES Country(country_id)
);

CREATE TABLE DiplomaticRelations (
    country_id_1 INT,
    country_id_2 INT,
    relation_value INT DEFAULT 0,
    has_alliance BOOLEAN DEFAULT FALSE,
    has_non_aggression_pact BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (country_id_1, country_id_2),
    FOREIGN KEY (country_id_1) REFERENCES Country(country_id),
    FOREIGN KEY (country_id_2) REFERENCES Country(country_id),
    CHECK (country_id_1 != country_id_2)
);

CREATE TABLE War (
    war_id INT PRIMARY KEY,
    war_name VARCHAR(100) NOT NULL,
    war_progress INT DEFAULT 0,
    start_tick INT NOT NULL
);

CREATE TABLE WarParticipants (
    war_id INT,
    country_id INT,
    is_attacker BOOLEAN,
    PRIMARY KEY (war_id, country_id),
    FOREIGN KEY (war_id) REFERENCES War(war_id),
    FOREIGN KEY (country_id) REFERENCES Country(country_id)
);

CREATE TABLE PopConsumptionNeed (
    pop_type_id INT,
    goods_id INT,
    amount_per_100k DECIMAL(10,4) NOT NULL, /* How much 100k pops demand per tick per province */
    FOREIGN KEY (pop_type_id) REFERENCES PopulationTypes(pop_id),
    FOREIGN KEY (goods_id) REFERENCES Goods(goods_id),
    PRIMARY KEY (pop_type_id, goods_id)
);