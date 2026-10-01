# CrimsonCart Receipts - IDOR Lab

A tiny, fully offline web challenge for teaching Insecure Direct Object
Reference (IDOR) / broken access control.

## Running it

Works the same way on **Windows, macOS, and Linux** - the app is pure
Python standard library, nothing OS-specific.

**macOS / Linux:**
```bash
./run.sh
```

**Windows:** double-click `run.bat`, or run it from a Command Prompt /
PowerShell:
```
run.bat
```

**Any OS, directly:**
```bash
python3 server.py
```
(on Windows this is usually just `python server.py`)

Your browser should open automatically to **http://localhost:8000/lab**.
If it doesn't, open that link manually.

No dependencies to install, nothing to `pip install`. Uses only Python's
standard library (`http.server`, `webbrowser`). No network access, no
database, no external files - everything the app needs is hardcoded in
`server.py`. Behavior is fully deterministic every run.

**Requirement:** Python 3.6+ must already be installed. Every current
Windows, macOS, and Linux system either ships with it or gets it from
https://python.org in under a minute.

## Hosting it online for a whole class (one shared link)

**GitHub Pages will not work for this.** Pages only serves static files -
it can't run `server.py`. Pushing this repo to Pages would just offer the
Python source as a plain-text download, not run the challenge, and would
hand out the answer key in the process. You need a host that keeps a real
Python process running.

**Easiest: Render.com (free tier)**
1. Push this folder to a GitHub repo.
2. On https://render.com, "New +" -> "Web Service" -> connect that repo.
3. Render auto-detects `render.yaml` in this folder - just confirm and deploy.
4. You get a stable link like `https://crimsoncart-lab.onrender.com/lab`
   to share with the whole class.

Free tier spins down after 15 minutes of no traffic and takes ~30-60
seconds to wake back up on the next visit - fine for homework, less ideal
for a timed in-class moment where everyone hits it at once cold.

**Fastest: Replit**
Upload `server.py` to a new Python Repl and hit Run - it prints a public
URL immediately. Free tier also sleeps after inactivity.

Either way, no code changes are needed - `server.py` already reads the
`PORT` environment variable these platforms set automatically, and only
tries to open a local browser window when running on your own machine.

## The challenge (student-facing)

Your receipt is at `/lab/receipt?id=1001`. It says receipts are private to
the buyer. Nobody checked whether the buyer asking is the buyer named.
There are a handful of receipts. One of them is not a student's.

**Hint:** The number in the address bar is doing more work than it should.

---

## Solution (instructor only - do not share with students)

**Vulnerability:** the server looks up a receipt purely by the numeric
`id` query parameter and returns it to whoever asks - there is no session,
no login, and no check that the requester is the person named on the
receipt. This is a textbook IDOR: an internal object reference (a
sequential database-style ID) is exposed directly in the URL and used as
the *only* access control.

**Solve path:**

1. Visit `/lab/receipt?id=1001` - a normal student receipt, labeled
   "Private - buyer only."
2. Notice nothing about who you are was ever checked - the page rendered
   immediately, with no login step.
3. Try adjacent IDs: `?id=1002`, `?id=1003`, `?id=1005` - all render fine,
   all different students' data, still with zero ownership check.
4. Try `?id=1004` - this receipt is not a student purchase (buyer role
   shows "Procurement Office," a large site-license order) and contains
   the flag:

   **FLAG:** `CRIMSON{ids_are_not_access_control}`

**Discussion points to raise after the reveal:**

- **Sequential IDs are guessable.** The receipt numbers count up by one -
  an attacker doesn't need to find anything, just increment.
- **The fix isn't hiding the ID.** Switching to a random-looking ID (a
  UUID) makes guessing harder but doesn't fix the actual bug - the server
  still has to check that the logged-in user owns the resource before
  returning it. Obscurity is not access control.
- **The real fix:** on every request, check `receipt.owner == current_user`
  server-side, and return 403/404 if it doesn't match - regardless of
  what ID was requested.
- **Real-world parallel:** this is the same bug class as some of the
  highest-impact "broken access control" findings in bug bounty programs -
  changing an order ID, invoice ID, or account ID in a URL and getting
  someone else's data back.
