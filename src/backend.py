"""
World Economy Backend - Database Management System
Automatic ticking of economic values every 5 seconds
"""

import os
import sys
from datetime import datetime
import threading
import time
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
import json
from pathlib import Path

try:
    import psycopg2  # type: ignore
    from psycopg2 import sql  # type: ignore
except ImportError:
    # Fallback for environments using psycopg v3 package name.
    import psycopg as psycopg2  # type: ignore
    from psycopg import sql  # type: ignore

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
@dataclass
class DatabaseConfig:
    """Database configuration, make sure to modify this on the basis of who's gonna present."""
    host: str = 'localhost'
    port: int = 5432
    database: str = 'world_economy'
    user: str = 'postgres'
    password: str = 'password'
class DatabaseConnection:
    """Handle database connections, simple as that."""
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection = None
        self._lock = threading.RLock()
        self.connect()
    
    def connect(self):
        """With this fool we can conquer the world."""
        try:
            self.connection = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password
            )
            self.connection.autocommit = False
            logger.info("Database connection established") #God bless the mighty logger
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute SELECT query, this is gonna be our toast and tingles."""
        try:
            with self._lock:
                cursor = self.connection.cursor()
                cursor.execute(query, params or ())
                columns = [desc[0] for desc in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                cursor.close()
                return results
        except psycopg2.Error as e:
            logger.error(f"Query execution error: {e}")
            return []
    def execute_update(self, query: str, params: tuple = None) -> bool:
        """Execute INSERT/UPDATE/DELETE query, this is gonna be our fish and chips."""
        try:
            with self._lock:
                cursor = self.connection.cursor()
                cursor.execute(query, params or ())
                self.connection.commit()
                logger.info(f"Update successful: {cursor.rowcount} rows affected")
                cursor.close()
                return True
        except psycopg2.Error as e:
            with self._lock:
                self.connection.rollback()
            logger.error(f"Update execution error: {e}")
            return False

    def execute_update_returning(self, query: str, params: tuple = None) -> Optional[Dict]:
        """Execute INSERT/UPDATE/DELETE query with RETURNING clause, this is our cup of tea. Damn, now I feel like I'm cooking a breakfast."""
        try:
            with self._lock:
                cursor = self.connection.cursor()
                cursor.execute(query, params or ())
                row = cursor.fetchone()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                self.connection.commit()
                cursor.close()
                if row is None or not columns:
                    return None
                return dict(zip(columns, row))
        except psycopg2.Error as e:
            with self._lock:
                self.connection.rollback()
            logger.error(f"Update(RETURNING) execution error: {e}")
            return None
    
    def close(self):
        """Close database connection, bai bai..."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")


class WorldEconomyAPI:
    """Main API for world economy database operations, don't touch this unless the program decides that it's existence is too much."""
    
    def __init__(self, db_config: DatabaseConfig):
        self.db = DatabaseConnection(db_config)
        self.ticker_active = False
        self.ticker_thread = None
        self._schema_cache: Dict[str, Any] = {}
    
    def get_all_countries(self) -> List[Dict]:
        """Get all countries, self explanatory."""
        query = "SELECT * FROM Country ORDER BY country_name"
        return self.db.execute_query(query)

    def get_country_options(self) -> List[Dict[str, Any]]:
        return self.db.execute_query(
            "SELECT country_id, country_name FROM Country ORDER BY country_name"
        )

    def get_province_options(self) -> List[Dict[str, Any]]:
        return self.db.execute_query(
            """
            SELECT p.province_id,
                   p.node_id,
                   c.country_name AS owner_country_name
            FROM Province p
            LEFT JOIN Country c ON c.country_id = p.owner_country_id
            ORDER BY p.province_id
            """
        )

    def get_goods_options(self) -> List[Dict[str, Any]]:
        return self.db.execute_query(
            "SELECT goods_id, good_name FROM Goods ORDER BY good_name"
        )

    def get_population_type_options(self) -> List[Dict[str, Any]]:
        return self.db.execute_query(
            "SELECT pop_id, pop_name FROM PopulationTypes ORDER BY pop_name"
        )

    def get_factory_type_options(self) -> List[Dict[str, Any]]:
        return self.db.execute_query(
            "SELECT factory_type_id, factory_name FROM FactoryType ORDER BY factory_name"
        )

    def get_map_node_options(self) -> List[Dict[str, Any]]:
        return self.db.execute_query(
            "SELECT node_id, node_name, terrain_type FROM MapNode ORDER BY node_id"
        )
    
    def get_country_by_id(self, country_id: int) -> Optional[Dict]:
        """Get country by ID, also self explanatory."""
        query = "SELECT * FROM Country WHERE country_id = %s"
        results = self.db.execute_query(query, (country_id,))
        return results[0] if results else None
    
    def get_country_by_name(self, name: str) -> Optional[Dict]:
        """Get country by name, man do we really need to write these stupid comments?"""
        query = "SELECT * FROM Country WHERE country_name = %s"
        results = self.db.execute_query(query, (name,))
        return results[0] if results else None
    
    def get_countries_above_avg_gdp(self) -> List[Dict]:
        query = """
            SELECT country_name, gdp
            FROM Country
            WHERE gdp > (SELECT AVG(gdp) FROM Country)
            ORDER BY gdp DESC
        """
        return self.db.execute_query(query)
    
    def get_countries_above_avg_gdp_per_capita(self) -> List[Dict]:
        # schemafinal.sql has no population in Country; use GDP ranking as a proxy.
        query = """
            SELECT country_name, gdp AS gdp_per_capita
            FROM Country
            ORDER BY gdp DESC
            LIMIT 10
        """
        return self.db.execute_query(query)

    def table_exists(self, table: str) -> bool:
        rows = self.db.execute_query(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema='public' AND table_name=%s
            LIMIT 1
            """,
            (table,),
        )
        return bool(rows)

    def list_tables(self) -> List[str]:
        rows = self.db.execute_query(
            """
            SELECT tablename
            FROM pg_catalog.pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
            """
        )
        return [r["tablename"] for r in rows]

    def run_sql_file(self, path: str) -> bool:
        """
        Execute a .sql file containing simple statements (INSERT/UPDATE/DELETE).
        This is intended for seed files like seed_2020.sql (no stored procedures).
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(str(p))
        sql_text = p.read_text(encoding="utf-8")
        return self.run_sql_script(sql_text)

    def run_sql_script(self, sql_text: str) -> bool:
        """
        Execute multiple SQL statements separated by ';'.
        Safe for seed scripts without function bodies.
        """
        statements = []
        buff = []
        in_single = False
        in_double = False

        for ch in sql_text:
            if ch == "'" and not in_double:
                in_single = not in_single
            elif ch == '"' and not in_single:
                in_double = not in_double

            if ch == ";" and not in_single and not in_double:
                stmt = "".join(buff).strip()
                buff = []
                if stmt:
                    statements.append(stmt)
            else:
                buff.append(ch)

        tail = "".join(buff).strip()
        if tail:
            statements.append(tail)

        try:
            with self.db._lock:
                cur = self.db.connection.cursor()
                for stmt in statements:
                    cur.execute(stmt)
                self.db.connection.commit()
                cur.close()
            return True
        except Exception as e:
            with self.db._lock:
                self.db.connection.rollback()
            logger.error(f"run_sql_script error: {e}")
            return False

    def get_table_columns(self, table: str) -> List[Dict[str, Any]]:
        cache_key = f"cols:{table}"
        if cache_key in self._schema_cache:
            return self._schema_cache[cache_key]

        rows = self.db.execute_query(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
            """,
            (table,),
        )
        self._schema_cache[cache_key] = rows
        return rows

    def get_table_primary_key_columns(self, table: str) -> List[str]:
        cache_key = f"pk:{table}"
        if cache_key in self._schema_cache:
            return self._schema_cache[cache_key]

        rows = self.db.execute_query(
            """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
            WHERE tc.table_schema='public'
              AND tc.table_name=%s
              AND tc.constraint_type='PRIMARY KEY'
            ORDER BY kcu.ordinal_position
            """,
            (table,),
        )
        pk = [r["column_name"] for r in rows]
        self._schema_cache[cache_key] = pk
        return pk

    def get_table_data(self, table: str, limit: int = 500) -> List[Dict]:
        cols = self.get_table_columns(table)
        if not cols:
            return []
        query = sql.SQL("SELECT * FROM {t} LIMIT {lim}").format(
            t=sql.Identifier(table),
            lim=sql.Literal(int(limit)),
        )
        try:
            with self.db._lock:
                cur = self.db.connection.cursor()
                cur.execute(query)
                colnames = [d[0] for d in cur.description]
                out = [dict(zip(colnames, row)) for row in cur.fetchall()]
                cur.close()
                return out
        except psycopg2.Error as e:
            logger.error(f"get_table_data error: {e}")
            return []

    def update_cell(self, table: str, pk_values: Dict[str, Any], column: str, value: Any) -> bool:
        pk_cols = self.get_table_primary_key_columns(table)
        if not pk_cols:
            raise ValueError(f"Table '{table}' has no primary key; cannot update safely.")
        if column in pk_cols:
            raise ValueError("Editing primary key columns is not supported in this UI.")
        if any(pk not in pk_values for pk in pk_cols):
            raise ValueError(f"Missing primary key values. Required: {pk_cols}")
        cols = {c["column_name"] for c in self.get_table_columns(table)}
        if column not in cols:
            raise ValueError(f"Unknown column '{column}' for table '{table}'.")
        where = sql.SQL(" AND ").join(
            sql.SQL("{c} = %s").format(c=sql.Identifier(pk)) for pk in pk_cols
        )
        query = sql.SQL("UPDATE {t} SET {col} = %s WHERE ").format(
            t=sql.Identifier(table),
            col=sql.Identifier(column),
        ) + where
        params = (value, *(pk_values[pk] for pk in pk_cols))
        try:
            with self.db._lock:
                cur = self.db.connection.cursor()
                cur.execute(query, params)
                self.db.connection.commit()
                cur.close()
                return True
        except psycopg2.Error as e:
            with self.db._lock:
                self.db.connection.rollback()
            logger.error(f"update_cell error: {e}")
            return False
    def insert_row(self, table: str, row: Dict[str, Any]) -> bool:
        cols_meta = self.get_table_columns(table)
        cols = [c["column_name"] for c in cols_meta]
        if not cols:
            raise ValueError(f"Unknown table '{table}'.")
        insert_cols = [c for c in cols if c in row]
        if not insert_cols:
            raise ValueError("No valid columns provided for insert.")
        query = sql.SQL("INSERT INTO {t} ({cols}) VALUES ({vals})").format(
            t=sql.Identifier(table),
            cols=sql.SQL(", ").join(sql.Identifier(c) for c in insert_cols),
            vals=sql.SQL(", ").join(sql.Placeholder() for _ in insert_cols),
        )
        params = tuple(row[c] for c in insert_cols)
        try:
            with self.db._lock:
                cur = self.db.connection.cursor()
                cur.execute(query, params)
                self.db.connection.commit()
                cur.close()
                return True
        except psycopg2.Error as e:
            with self.db._lock:
                self.db.connection.rollback()
            logger.error(f"insert_row error: {e}")
            return False

    def delete_row(self, table: str, pk_values: Dict[str, Any]) -> bool:
        pk_cols = self.get_table_primary_key_columns(table)
        if not pk_cols:
            raise ValueError(f"Table '{table}' has no primary key; cannot delete safely.")
        if any(pk not in pk_values for pk in pk_cols):
            raise ValueError(f"Missing primary key values. Required: {pk_cols}")

        where = sql.SQL(" AND ").join(
            sql.SQL("{c} = %s").format(c=sql.Identifier(pk)) for pk in pk_cols
        )
        query = sql.SQL("DELETE FROM {t} WHERE ").format(t=sql.Identifier(table)) + where
        params = tuple(pk_values[pk] for pk in pk_cols)
        try:
            with self.db._lock:
                cur = self.db.connection.cursor()
                cur.execute(query, params)
                self.db.connection.commit()
                cur.close()
                return True
        except psycopg2.Error as e:
            with self.db._lock:
                self.db.connection.rollback()
            logger.error(f"delete_row error: {e}")
            return False

    def next_int_id(self, table: str, id_column: str) -> int:
        q = sql.SQL("SELECT COALESCE(MAX({c}), 0) + 1 AS next_id FROM {t}").format(
            c=sql.Identifier(id_column),
            t=sql.Identifier(table),
        )
        try:
            with self.db._lock:
                cur = self.db.connection.cursor()
                cur.execute(q)
                nxt = int(cur.fetchone()[0])
                cur.close()
                return nxt
        except Exception as e:
            logger.error(f"next_int_id error: {e}")
            return 1

    def create_country(
        self,
        name: str,
        gdp: float,
        national_debt: float = 0.0,
        government_type_id: Optional[int] = None,
        currency_id: Optional[int] = None,
    ) -> bool:
        country_id = self.next_int_id("Country", "country_id")
        return self.insert_row(
            "Country",
            {
                "country_id": country_id,
                "country_name": name,
                "gdp": gdp,
                "national_debt": national_debt,
                "government_type_id": government_type_id,
                "currency_id": currency_id,
            },
        )

    def create_province(self, node_id: int, owner_country_id: int, controller_country_id: int) -> bool:
        province_id = self.next_int_id("Province", "province_id")
        return self.insert_row(
            "Province",
            {
                "province_id": province_id,
                "node_id": node_id,
                "owner_country_id": owner_country_id,
                "controller_country_id": controller_country_id,
            },
        )

    def add_province_population(
        self,
        province_id: int,
        pop_type_id: int,
        headcount: int,
        wealth: float = 0.0,
        militancy: float = 0.0,
    ) -> bool:
        province_pop_id = self.next_int_id("ProvincePopulation", "province_pop_id")
        return self.insert_row(
            "ProvincePopulation",
            {
                "province_pop_id": province_pop_id,
                "province_id": province_id,
                "pop_type_id": pop_type_id,
                "headcount": headcount,
                "wealth": wealth,
                "militancy": militancy,
            },
        )

    def create_province_factory(self, province_id: int, factory_type_id: int, is_active: bool = True) -> bool:
        factory_instance_id = self.next_int_id("ProvinceFactory", "factory_instance_id")
        return self.insert_row(
            "ProvinceFactory",
            {
                "factory_instance_id": factory_instance_id,
                "province_id": province_id,
                "factory_type_id": factory_type_id,
                "is_active": is_active,
            },
        )

    def create_market_order(
        self,
        country_id: int,
        goods_id: int,
        is_buy_order: bool,
        quantity: int,
        tick_submitted: int,
    ) -> bool:
        order_id = self.next_int_id("MarketOrders", "order_id")
        return self.insert_row(
            "MarketOrders",
            {
                "order_id": order_id,
                "country_id": country_id,
                "goods_id": goods_id,
                "is_buy_order": is_buy_order,
                "quantity": quantity,
                "fulfilled_quantity": 0,
                "tick_submitted": tick_submitted,
            },
        )

    def create_active_trade_route(
        self,
        buyer_country_id: int,
        seller_country_id: int,
        goods_id: int,
        quantity: int,
        tick_established: int,
        route_efficiency: float = 1.0,
    ) -> bool:
        route_id = self.next_int_id("ActiveTradeRoute", "route_id")
        return self.insert_row(
            "ActiveTradeRoute",
            {
                "route_id": route_id,
                "buyer_country_id": buyer_country_id,
                "seller_country_id": seller_country_id,
                "goods_id": goods_id,
                "quantity": quantity,
                "route_efficiency": route_efficiency,
                "tick_established": tick_established,
            },
        )

    def start_war(
        self,
        war_name: str,
        start_tick: int,
        participants: List[Dict[str, Any]],
    ) -> bool:
        """Create a war and war participants from schemafinal.sql."""
        war_id = self.next_int_id("War", "war_id")
        ok = self.insert_row(
            "War",
            {
                "war_id": war_id,
                "war_name": war_name,
                "war_progress": 0,
                "start_tick": start_tick,
            },
        )
        if not ok:
            return False

        for p in participants:
            cid = int(p["country_id"])
            is_attacker = bool(p.get("is_attacker", False))
            okp = self.insert_row(
                "WarParticipants",
                {"war_id": war_id, "country_id": cid, "is_attacker": is_attacker},
            )
            if not okp:
                return False
        return True
    
    def get_countries_with_highest_casualties(self, limit: int = 2) -> List[Dict]:
        query = """
            SELECT c.country_name,
                   COUNT(wp.war_id) AS wars_joined
            FROM Country c
            JOIN WarParticipants wp ON c.country_id = wp.country_id
            GROUP BY c.country_id, c.country_name
            ORDER BY wars_joined DESC
            LIMIT %s
        """
        return self.db.execute_query(query, (limit,))
    
    def get_countries_never_in_war(self) -> List[Dict]:
        query = """
            SELECT c.country_name
            FROM Country c
            LEFT JOIN WarParticipants wp ON c.country_id = wp.country_id
            WHERE wp.country_id IS NULL
        """
        return self.db.execute_query(query)
    
    def get_longest_war(self) -> Optional[Dict]:
        query = """
            SELECT war_id, war_name, war_progress
            FROM War
            ORDER BY war_progress DESC
            LIMIT 1
        """
        results = self.db.execute_query(query)
        return results[0] if results else None
    
    def get_average_manpower_loss_per_war(self) -> List[Dict]:
        query = """
            SELECT w.war_id,
                   COUNT(wp.country_id) AS participants_count
            FROM War w
            JOIN WarParticipants wp ON w.war_id = wp.war_id
            GROUP BY w.war_id
            ORDER BY w.war_id
        """
        return self.db.execute_query(query)
    
    def get_total_production_value_per_country(self) -> List[Dict]:
        query = """
            SELECT c.name,
                   SUM(p.quantity * g.base_price) AS total_production_value
            FROM Country c
            JOIN Production p ON c.country_id = p.country_id
            JOIN Goods g ON p.goods_id = g.goods_id
            GROUP BY c.country_id, c.name
            ORDER BY total_production_value DESC
        """
        return self.db.execute_query(query)
    
    def get_most_produced_goods_by_category(self) -> List[Dict]:
        query = """
            SELECT g.category,
                   SUM(p.quantity) AS total_quantity
            FROM Production p
            JOIN Goods g ON p.goods_id = g.goods_id
            GROUP BY g.category
            ORDER BY total_quantity DESC
        """
        return self.db.execute_query(query)
    
    def get_countries_with_highest_production(self, limit: int = 5) -> List[Dict]:
        query = """
            SELECT c.name,
                   SUM(p.quantity) AS total_production
            FROM Country c
            JOIN Production p ON c.country_id = p.country_id
            GROUP BY c.country_id, c.name
            ORDER BY total_production DESC
            LIMIT %s
        """
        return self.db.execute_query(query, (limit,))
    
    def get_countries_producing_more_than_consuming(self) -> List[Dict]:
        query = """
            SELECT c.name,
                   SUM(p.quantity) AS total_production,
                   SUM(cons.quantity) AS total_consumption
            FROM Country c
            JOIN Production p ON c.country_id = p.country_id
            JOIN Consumption cons ON c.country_id = cons.country_id
            GROUP BY c.country_id, c.name
            HAVING SUM(p.quantity) > SUM(cons.quantity)
            ORDER BY SUM(p.quantity) DESC
        """
        return self.db.execute_query(query)
    
    def get_goods_produced_but_not_consumed(self) -> List[Dict]:
        query = """
            SELECT g.name
            FROM Goods g
            JOIN Production p ON g.goods_id = p.goods_id
            WHERE NOT EXISTS (
                SELECT 1
                FROM Consumption c
                WHERE c.goods_id = g.goods_id
            )
        """
        return self.db.execute_query(query)
    
    def get_trade_between_countries(self) -> List[Dict]:
        query = """
            SELECT c1.country_name AS buyer,
                   c2.country_name AS seller,
                   g.good_name AS goods,
                   t.quantity,
                   t.route_efficiency
            FROM ActiveTradeRoute t
            JOIN Country c1 ON t.buyer_country_id = c1.country_id
            JOIN Country c2 ON t.seller_country_id = c2.country_id
            JOIN Goods g ON t.goods_id = g.goods_id
            ORDER BY t.route_id
        """
        return self.db.execute_query(query)
    
    
    def get_dark_economy_countries(self) -> List[Dict]:
        # schemafinal.sql has no DarkEconomy table; keep API compatible by returning empty list.
        return []
    
    def get_average_tax_rate_per_country(self) -> List[Dict]:
        query = """
            SELECT c.name,
                   AVG(sc.tax_rate) AS avg_tax_rate
            FROM Country c
            LEFT JOIN CountrySocialClass csc ON c.country_id = csc.country_id
            LEFT JOIN SocialClass sc ON csc.class_id = sc.class_id
            GROUP BY c.country_id, c.name
            ORDER BY avg_tax_rate DESC
        """
        return self.db.execute_query(query)
    
    
    def get_friendly_relations(self) -> List[Dict]:
        query = """
            SELECT DISTINCT c.name
            FROM Country c
            JOIN Diplomacy d ON c.country_id = d.country1_id
                             OR c.country_id = d.country2_id
            WHERE d.relation_type = 'Friendly'
        """
        return self.db.execute_query(query)
    
    
    def tick_economy(self):
        logger.info("Starting economy tick cycle")
        
        try:
            if self.table_exists("Country"):
                # Minimal deterministic tick for the new schema:
                # apply very small debt interest and GDP growth.
                self.db.execute_update(
                    """
                    UPDATE Country
                    SET national_debt = national_debt * 1.0005,
                        gdp = gdp * 1.0008
                    """
                )

            logger.info("Economy tick completed successfully")
            
            self._log_economy_status()
            
        except Exception as e:
            logger.error(f"Error during economy tick: {e}")
    
    def _log_economy_status(self):
        countries = self.get_all_countries()
        total_gdp = sum(float(c.get('gdp', 0)) for c in countries)
        
        logger.info(f"Total countries: {len(countries)}, Total Global GDP: ${total_gdp:,.2f}")
    
    def start_ticker(self, interval: int = 1):
        if self.ticker_active:
            logger.warning("Ticker is already running")
            return
        
        self.ticker_active = True
        self.ticker_thread = threading.Thread(
            target=self._ticker_loop,
            args=(interval,),
            daemon=True
        )
        self.ticker_thread.start()
        logger.info(f"Economy ticker started with {interval}s interval")
    
    def _ticker_loop(self, interval: int):
        while self.ticker_active:
            try:
                self.tick_economy()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Ticker loop error: {e}")
                time.sleep(interval)
    
    def stop_ticker(self):
        if not self.ticker_active:
            logger.warning("Ticker is not running")
            return
        
        self.ticker_active = False
        if self.ticker_thread:
            self.ticker_thread.join(timeout=10)
        logger.info("Economy ticker stopped")
    
    def get_ticker_status(self) -> Dict[str, Any]:
        return {
            'is_active': self.ticker_active,
            'thread_alive': self.ticker_thread.is_alive() if self.ticker_thread else False,
            'timestamp': datetime.now().isoformat()
        }
    
    
    def generate_economy_report(self) -> Dict[str, Any]:
        return {
            'timestamp': datetime.now().isoformat(),
            'total_countries': len(self.get_all_countries()),
            'countries_above_avg_gdp': len(self.get_countries_above_avg_gdp()),
            'active_wars': len(self.get_table_data("War", limit=500)) if self.table_exists("War") else 0,
            'active_trade_routes': len(self.get_table_data("ActiveTradeRoute", limit=500)) if self.table_exists("ActiveTradeRoute") else 0,
            'provinces': len(self.get_table_data("Province", limit=5000)) if self.table_exists("Province") else 0,
            'longest_war': self.get_longest_war(),
            'ticker_status': self.get_ticker_status()
        }
    
    def cleanup(self):
        self.stop_ticker()
        self.db.close()

    # ==================== TRANSACTION DEMO (UI BUTTONS) ====================

    def demo_trade_transaction(self, conflict: bool) -> Dict[str, Any]:
        """
        Create trade routes among 3 countries inside a single SQL transaction.

        - conflict=True: intentionally triggers a PK conflict on ActiveTradeRoute.route_id
          so the entire transaction is rolled back and an error is returned.
        - conflict=False: uses unique route_ids and commits successfully.
        """
        if not self.table_exists("ActiveTradeRoute"):
            return {"ok": False, "message": "ActiveTradeRoute table not found. Did you apply schemafinal.sql?"}

        countries = self.db.execute_query(
            "SELECT country_id, country_name FROM Country ORDER BY random() LIMIT 3"
        )
        if len(countries) < 3:
            return {"ok": False, "message": "Need at least 3 countries seeded first."}

        goods = self.db.execute_query("SELECT goods_id, good_name FROM Goods ORDER BY random() LIMIT 1")
        if not goods:
            return {"ok": False, "message": "Need goods seeded first."}

        a, b, c = countries
        goods_id = int(goods[0]["goods_id"])

        # Two routes: A buys from B, B buys from C (three countries involved)
        buyer_1, seller_1 = int(a["country_id"]), int(b["country_id"])
        buyer_2, seller_2 = int(b["country_id"]), int(c["country_id"])

        quantity_1 = int(1000 + (time.time_ns() % 50000))
        quantity_2 = int(1500 + (time.time_ns() % 60000))
        tick_established = int(time.time()) % 100000
        eff_1 = 0.95
        eff_2 = 0.90

        try:
            with self.db._lock:
                cur = self.db.connection.cursor()

                if conflict:
                    # Use an existing route_id if present; otherwise create one first.
                    cur.execute("SELECT route_id FROM ActiveTradeRoute ORDER BY route_id LIMIT 1")
                    row = cur.fetchone()
                    if row:
                        route_id = int(row[0])
                    else:
                        route_id = self.next_int_id("ActiveTradeRoute", "route_id")
                        cur.execute(
                            """
                            INSERT INTO ActiveTradeRoute
                              (route_id, buyer_country_id, seller_country_id, goods_id, quantity, route_efficiency, tick_established)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """,
                            (route_id, buyer_1, seller_1, goods_id, quantity_1, eff_1, tick_established),
                        )

                    # Now intentionally conflict by inserting the SAME route_id again.
                    cur.execute(
                        """
                        INSERT INTO ActiveTradeRoute
                          (route_id, buyer_country_id, seller_country_id, goods_id, quantity, route_efficiency, tick_established)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (route_id, buyer_2, seller_2, goods_id, quantity_2, eff_2, tick_established + 1),
                    )
                else:
                    route_id_1 = self.next_int_id("ActiveTradeRoute", "route_id")
                    route_id_2 = route_id_1 + 1

                    cur.execute(
                        """
                        INSERT INTO ActiveTradeRoute
                          (route_id, buyer_country_id, seller_country_id, goods_id, quantity, route_efficiency, tick_established)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (route_id_1, buyer_1, seller_1, goods_id, quantity_1, eff_1, tick_established),
                    )
                    cur.execute(
                        """
                        INSERT INTO ActiveTradeRoute
                          (route_id, buyer_country_id, seller_country_id, goods_id, quantity, route_efficiency, tick_established)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (route_id_2, buyer_2, seller_2, goods_id, quantity_2, eff_2, tick_established + 1),
                    )

                self.db.connection.commit()
                cur.close()

            if conflict:
                # If we reached here, conflict didn't happen (unexpected).
                return {"ok": False, "message": "Expected a conflict, but transaction committed."}

            return {
                "ok": True,
                "message": f"Committed trade routes among {a['country_name']}, {b['country_name']}, {c['country_name']}.",
            }
        except Exception as e:
            with self.db._lock:
                self.db.connection.rollback()
            return {"ok": False, "message": f"Transaction rolled back due to SQL error: {e}"}


def main():
    logger.info("Initializing World Economy Backend")
    
    # Database configuration
    db_config = DatabaseConfig(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        database=os.getenv('DB_NAME', 'world_economy'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'password')
    )
    
    # Initialize API
    api = WorldEconomyAPI(db_config)
    
    try:
        # Start automatic ticker (ticks every 5 seconds)
        api.start_ticker(interval=5)
        
        # Example: Run for demonstration
        logger.info("Backend is running. Press Ctrl+C to stop.")
        
        # Keep the application running
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
    
    finally:
        api.cleanup()
        logger.info("Backend shutdown complete")


if __name__ == '__main__':
    main()
