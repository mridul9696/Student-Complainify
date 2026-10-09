# Complainify Fixes - Taught Like a Friend

You fixed P0 to P3. This file teaches you WHAT was wrong, WHY it matters, WHAT we changed, and HOW to check it works. No hard words.

Think of your app like a school office:
- Students submit papers (complaints)
- Admins sort and reply
- Database = filing cabinet
- Server = office building

---

## P0 - House on Fire (if you ignore, hackers come)

### 1. Password written in code - `backend/app.py:35-47`

**Story:** You wrote your house key on the front door. Anyone who sees the code sees your Gmail password `vksq mrdy qnqd zbut`.

**Before:**
```python
app.secret_key = 'supersecretkey'
SMTP_USER = 'brooskings661@gmail.com'
SMTP_PASS = 'vksq mrdy qnqd zbut'
```

**After:**
```python
app.secret_key = os.environ.get('SECRET_KEY')  # reads from .env file
SMTP_USER = os.environ.get('SMTP_USER', '')    # empty if no .env
SMTP_PASS = os.environ.get('SMTP_PASS', '')
```

**How to check:**
1. Open `backend/app.py`, you should NOT see your real password.
2. Open `.env`, you SHOULD see it there. `.env` never goes to GitHub.

**Lesson:** Code = public. `.env` = private diary.

---

### 2. Passwords saved in plain text - `backend/app.py:96`

**Story:** You kept student passwords in a notebook anyone can read. Plus you locked with a weak lock (SHA256 with no salt = same password always makes same code).

**Before:**
```python
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()  # weak, no salt

# saved both:
# password = sha256(pw), plain_password = pw (real password!)
```

**After:**
```python
def hash_pw(pw):
    return generate_password_hash(pw)  # scrypt + salt, different every time

def verify_pw(stored, pw):
    # new scrypt? check it. old sha256? still accept for old users.
```

And we deleted column `plain_password` from DB.

**How to check:**
```sql
DESCRIBE users;  -- no plain_password line = good
```
Login still works for old + new users.

**Lesson:** Never save real password. Save salted soup that cannot be reversed.

---

### 3. Retrain button open to all - `backend/app.py:1870`

**Story:** You left a big heavy machine ON outside. Anyone walking by can press START and your electricity goes off (server hangs 180 sec).

**Before:**
```python
@app.route('/api/retrain', methods=['POST'])
def api_retrain():
    # no check! anyone can run
```

**After:**
```python
def api_retrain():
    if not login_required('admin'):
        return {'error': 'Unauthorized'}, 403
```

**How to check:** Open new browser (not logged in), try POST to `/api/retrain`. You get 403.

**Lesson:** Heavy work = admin only.

---

### 4. One error deletes 3 tables - `backend/app.py:148`

**Story:** One light bulb fails, you burn the whole house to fix it. Old code did `DROP TABLE` if insert failed.

**Before:**
```python
except:
    DROP TABLE audit_logs, notifications, complaint_comments  # DATA LOST!
    CREATE TABLE ...  # empty tables
```

**After:**
```python
except:
    CREATE TABLE IF NOT EXISTS ...  # only create if missing, never delete
```

**How to check:** Open code, search `DROP TABLE`. Should be zero results in `log_action`.

**Lesson:** Never delete to fix. Only create if missing.

---

### 5. Files open to all - `backend/app.py:1885`

**Story:** Student documents kept in open basket. Guess file name, download it.

**Before:**
```python
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_file(filename)  # no login!
```

**After:**
```python
def uploaded_file(filename):
    if 'user_id' not in session:
        return redirect(index)
    if student and file not owned by you:
        return "Not authorized"
```

**How to check:** Logout, try `http://127.0.0.1:5000/uploads/some.pdf`. Must redirect to home.

**Lesson:** Check ID card before giving files.

---

### 6. Ticket ID too short - `backend/app.py:108`

**Story:** Giving roll numbers 1-100 to 10,000 students. Two get same number.

Old: `os.urandom(2)` = 2 bytes = 65,000 combos.
New: `os.urandom(4)` = 4 bytes = 4,000,000,000 combos.

```python
return 'CMP-' + os.urandom(4).hex().upper()  # e.g. CMP-A1B2C3D4
```

---

## P1 - Engine Broken (app crashes or gives wrong answer)

### 7. Half database - `backend/app.py:2023`

Old `init_db()` made only 3 tables. New install crashed because `users`, `complaints`, `otps`, `colleges` missing.

Now it creates all 7. Like building house with bathroom, kitchen, all rooms.

Check: fresh DB + run app = no `Table doesn't exist` error.

### 8. Retrain crash - `backend/app.py:1798`

Old: `json.loads(stdout)` - if retrain prints one extra warning line, crash.

New helper:
```python
def _run_retrain_script():
    # find LAST line starting with {, parse only that
```

Like reading only last page of letter, ignoring scribbles. Both admin button and API use same helper.

### 9. PDF crash - `backend/app.py:1285`

Old: `execute(sql, None)` when no filter. pymysql expects list, not None. Crash.

New: always pass `params` list (empty list is ok).

### 10. Stuck Pending - `backend/app.py:318`

Old logic:
```python
if email_exists and category != Other: In Progress
else: Pending
```
`Infrastructure` had no email, so always Pending forever.

New logic:
```python
if category != Other: In Progress
else: Pending
# email missing = just no mail, not stuck
```
Plus added `Infrastructure` email slot.

### 11. Big files - `backend/app.py:271`

Old: only checked `.pdf` ending. 1GB movie renamed to `.pdf` passes.

New: `MAX_UPLOAD_MB=10`, check actual size with `seek/tell`, reject with message.

### 12. Missing shopping list - `requirements.txt`

Charts need `matplotlib` but list didn't have it. New computer install failed. Added `matplotlib>=3.5`.

---

## P2 - Leaky Pipe (works now, breaks later)

### 13. Tap left open - DB connections

Old:
```python
conn = get_db(); cur = conn.cursor()
cur.execute(...)  # if error here, close never runs
cur.close(); conn.close()
```

New:
```python
conn = get_db(); cur = conn.cursor()
try:
    cur.execute(...)
finally:
    cur.close(); conn.close()  # always runs
```
Fixed in dashboards + assign + status + forgot-password.

### 14. Waiting for postman

Old: submit waited 30 sec x 2 for emails. User stared at loading.

New: timeout 10 sec, dept mail in background thread:
```python
send_email_background(...)  # returns instantly, sends in back
```
Student mail stays sync because we need to set `email_sent=1`.

### 15. Safety checks

- Forgot password: never show OTP on screen. Same message whether email exists or not (so hacker cannot guess emails). Max 3 OTPs per 10 min.
- Register: email must be `a@b.com`, phone 7-15 digits. Before `aaaa@` passed.
- Assign: rejects bad department name.
- Cookies: `HTTPONLY, SAMESITE=Lax`. Headers: `X-Frame-Options: DENY` etc.
- `debug=False` unless `FLASK_DEBUG=1`. Debug shows secrets.

Full CSRF tokens still need form edits - next step.

---

## P3 - Cleaning (90% of problems.txt)

`problems.txt` was VS Code lint, not real bugs. Mostly:

- `E702`: `a(); b()` on one line -> split to 2 lines. Same work, clean look.
- `E401`: `import a, b` -> 2 lines.
- `E701`: `if x: y` -> 2 lines.
- `F401`: removed unused `auto_categorize`, `secure_filename`.
- `F841`: removed unused `dept_name, sent, resolved_cnt`.
- `E741`: `l` -> `label` (l looks like 1).
- `E402`: added `# noqa: E402` because ml imports MUST stay after `sys.path`.

Now `ruff check All passed!`

---

## Extra we did together

- `.env.example`: added `MAX_UPLOAD_MB, COOKIE_SECURE, FLASK_DEBUG`.
- `.gitignore`: was a FOLDER by mistake, fixed to FILE. Now ignores `.env, uploads/, __pycache__/`.
- `complainify.sql`: removed `plain_password`.
- Frontend `submit_complaint.html`: added `escapeHtml()` for similar complaints. Before `s.subject` (user typed) went straight to `innerHTML` = XSS. Now escaped.

---

## How to prove everything works

```powershell
cd 'D:\PROJECT\6\Mridul\Student-Complainify\ComplaintMgmtSystem'
python -m py_compile backend\app.py  # OK
ruff check backend\app.py --no-cache  # All passed
$env:PYTHONPATH='D:\PROJECT\6\Mridul\Student-Complainify'
python -m pytest tests -p no:cacheprovider -q  # 30 passed
python backend\app.py  # open http://127.0.0.1:5000
```

Manual: Register > Submit with PDF > Track shows `In Progress` > Admin assign > Resolve.

You did P0-P3. Great work.
