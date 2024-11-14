# (c) 2024 Christoffer Wittchen
# Released under the MIT License.

import interactions
from cogs.miscellaneous import log_message

from utils.yaml_file import id_map

class Automations(interactions.Extension):
    def __init__(self, client):
        self.client: interactions.Client = client

    #region - MEMBER UPDATE LISTENER
    @interactions.listen()
    async def on_member_update(self, member_update: interactions.events.MemberUpdate):
        if member_update.before.pending and not member_update.after.pending:
            await member_update.after.add_role(id_map["member_role"])
            await log_message(self, f"{member_update.after.mention} accepterede reglerne.")
    #endregion

def setup(client):
    Automations(client)