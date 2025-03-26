# (c) 2025 Christoffer Wittchen
# Released under the MIT License.

from utils.database import DatabaseManager, QueryType

class GiveawayManager:
    """ Initialize the class with the database manager. """
    db = DatabaseManager()

    @staticmethod
    async def create_giveaway(message_id: int, data: dict):
        """ Creates a new giveaway with the given ID and data. """
        _query = f"CREATE TABLE g{message_id} ( id BIGINT PRIMARY KEY, user_name TEXT );"
        await GiveawayManager.db.execute_query(query = _query, query_type = QueryType.COMMIT)
        columns = ", ".join(data.keys())
        values = ", ".join(["%s"] * len(data))
        _query1 = f"INSERT INTO giveaways ({columns}) VALUES ({values});"
        await GiveawayManager.db.execute_query(query = _query1, params = tuple(data.values()), query_type = QueryType.COMMIT)

    @staticmethod
    async def get_active_giveaways():
        """ Fetches all active giveaways. """
        _query = "SELECT * FROM giveaways WHERE active = 1;"
        return await GiveawayManager.db.execute_query(query = _query, query_type = QueryType.FETCH_ALL)

    @staticmethod
    async def get_all_entries(id: int):
        """ Fetches all entries for a giveaway. """
        _query = f"SELECT id FROM g{id};"
        rows = await GiveawayManager.db.execute_query(query = _query, query_type = QueryType.FETCH_ALL)
        return [row["id"] for row in rows]

    @staticmethod
    async def add_entry(id: int, data: dict):
        """ Add a user to a giveaway. """
        columns = ", ".join(data.keys())
        values = ", ".join(["%s"] * len(data))
        _query = f"INSERT INTO g{id} ({columns}) VALUES ({values});"
        await GiveawayManager.db.execute_query(query = _query, params = tuple(data.values()), query_type = QueryType.COMMIT)
        _query1 = f"UPDATE giveaways SET entries = (SELECT COUNT(*) FROM g{id}) WHERE id = %s;"
        await GiveawayManager.db.execute_query(query = _query1, params = (id), query_type = QueryType.COMMIT)

    @staticmethod
    async def remove_entry(id: int, user_id: int):
        """ Remove a user from a giveaway. """
        _query = f"DELETE FROM g{id} WHERE id = %s;"
        await GiveawayManager.db.execute_query(query = _query, params = (user_id), query_type = QueryType.COMMIT)
        _query1 = f"UPDATE giveaways SET entries = (SELECT COUNT(*) FROM g{id}) WHERE id = %s;"
        await GiveawayManager.db.execute_query(query = _query1, params = (id), query_type = QueryType.COMMIT)

    @staticmethod
    async def select_winners(id: int, limit: int):
        """ Selects random winners from the entries. """
        _query = f"SELECT id FROM g{id} ORDER BY RAND() LIMIT {limit};"
        rows = await GiveawayManager.db.execute_query(query = _query, query_type = QueryType.FETCH_ALL)
        if rows:
            _query1 = f"DELETE FROM g{id} WHERE id = %s;"
            for row in rows:
                await GiveawayManager.db.execute_query(query = _query1, params = (row["id"]), query_type = QueryType.COMMIT)
            return [row["id"] for row in rows]
        return ["None"]

    @staticmethod
    async def mark_as_completed(id: int):
        """ Marks a giveaway as completed. """
        _query = f"UPDATE giveaways SET active = 0 WHERE id = %s;"
        await GiveawayManager.db.execute_query(query = _query, params = (id), query_type = QueryType.COMMIT)

    @staticmethod
    async def delete_giveaway(id: int):
        """ Drops the entries table for a giveaway. """
        _query = f"DROP TABLE IF EXISTS g{id};"
        await GiveawayManager.db.execute_query(query = _query, query_type = QueryType.COMMIT)
