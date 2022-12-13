# cncnet-qm-bot
CnCNet QM Discord Bot, in python

---
#### Developer notes:
- Create file named `.env` in `/cncnet-qm-bot/` directory
- Add discord application id `DISCORD_CLIENT_SECRET=[token]`
---
#### Bot Commands
- `!maps {ladder}` return the current QM maps of a given ladder
---
#### Bot Schedules
- 60 second interval: Send current QM player information to `qm-bot` channel
- Every 8 hours: Update discord users QM role according to their current QM rank
