from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_file
)

import sqlite3
import os
from io import BytesIO

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from werkzeug.utils import secure_filename

from cryptography.fernet import Fernet


# =========================================================
# APP CONFIGURATION
# =========================================================

app = Flask(__name__)

app.secret_key = "digital-memory-vault-secret-key"

DATABASE = os.path.join(
    app.root_path,
    "vault.db"
)


# =========================================================
# UPLOAD FOLDER
# =========================================================

UPLOAD_FOLDER = os.path.join(
    app.root_path,
    "uploads",
    "encrypted"
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Maximum upload size = 50 MB
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024


# =========================================================
# ENCRYPTION
# =========================================================

KEY_FILE = os.path.join(
    app.root_path,
    "secret.key"
)


def create_encryption_key():

    if not os.path.exists(KEY_FILE):

        key = Fernet.generate_key()

        with open(KEY_FILE, "wb") as file:
            file.write(key)

        return key

    with open(KEY_FILE, "rb") as file:
        return file.read()


ENCRYPTION_KEY = create_encryption_key()

cipher = Fernet(ENCRYPTION_KEY)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_database():

    connection = get_db()

    # -----------------------------------------------------
    # USERS TABLE
    # -----------------------------------------------------

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL

        )
    """)

    # -----------------------------------------------------
    # FILES TABLE
    # -----------------------------------------------------

    connection.execute("""
        CREATE TABLE IF NOT EXISTS files (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            original_name TEXT NOT NULL,

            stored_name TEXT NOT NULL,

            category TEXT NOT NULL,

            FOREIGN KEY(user_id)
            REFERENCES users(id)

        )
    """)

    # -----------------------------------------------------
    # NOTES TABLE
    # -----------------------------------------------------

    connection.execute("""
        CREATE TABLE IF NOT EXISTS notes (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            title TEXT NOT NULL,

            content TEXT NOT NULL,

            created_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(user_id)
            REFERENCES users(id)

        )
    """)

    connection.commit()

    connection.close()


# Initialize database
init_database()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    if "user_id" in session:

        return redirect(
            url_for("dashboard")
        )

    return redirect(
        url_for("login")
    )


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        # Check empty fields
        if not username or not password:

            flash(
                "Please fill all required fields."
            )

            return redirect(
                url_for("register")
            )

        # Check password match
        if password != confirm_password:

            flash(
                "Passwords do not match."
            )

            return redirect(
                url_for("register")
            )

        # Minimum password length
        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters."
            )

            return redirect(
                url_for("register")
            )

        # Hash password
        hashed_password = generate_password_hash(
            password
        )

        connection = get_db()

        try:

            connection.execute(
                """
                INSERT INTO users
                (
                    username,
                    password
                )
                VALUES (?, ?)
                """,
                (
                    username,
                    hashed_password
                )
            )

            connection.commit()

            flash(
                "Account created successfully!"
            )

            return redirect(
                url_for("login")
            )

        except sqlite3.IntegrityError:

            flash(
                "Username already exists."
            )

            return redirect(
                url_for("register")
            )

        finally:

            connection.close()

    return render_template(
        "register.html"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        connection = get_db()

        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

        connection.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session.clear()

            session["user_id"] = user["id"]

            session["username"] = user["username"]

            flash(
                "Login successful!"
            )

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid username or password."
        )

    return render_template(
        "login.html"
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    connection = get_db()

    # Get user's files
    files = connection.execute(
        """
        SELECT *
        FROM files
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    # Count documents
    document_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM files
        WHERE user_id = ?
        """,
        (session["user_id"],)
    ).fetchone()[0]

    # Count notes
    note_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM notes
        WHERE user_id = ?
        """,
        (session["user_id"],)
    ).fetchone()[0]

    connection.close()

    return render_template(
        "dashboard.html",
        username=session["username"],
        files=files,
        document_count=document_count,
        note_count=note_count
    )


# =========================================================
# MY VAULT
# =========================================================

@app.route("/vault")
def vault():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    connection = get_db()

    files = connection.execute(
        """
        SELECT *
        FROM files
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    connection.close()

    return render_template(
        "vault.html",
        username=session["username"],
        files=files
    )


# =========================================================
# UPLOAD
# =========================================================

@app.route("/upload", methods=["GET", "POST"])
def upload():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    # -----------------------------------------------------
    # OPEN UPLOAD PAGE
    # -----------------------------------------------------

    if request.method == "GET":

        return render_template(
            "upload.html"
        )

    # -----------------------------------------------------
    # GET FILE
    # -----------------------------------------------------

    uploaded_file = request.files.get(
        "file"
    )

    category = request.form.get(
        "category",
        "Other"
    ).strip()

    if not category:

        category = "Other"

    # No file
    if uploaded_file is None:

        flash(
            "Please select a file."
        )

        return redirect(
            url_for("upload")
        )

    # Empty filename
    if uploaded_file.filename == "":

        flash(
            "Please select a file."
        )

        return redirect(
            url_for("upload")
        )

    # Secure filename
    original_name = secure_filename(
        uploaded_file.filename
    )

    if not original_name:

        flash(
            "Invalid file name."
        )

        return redirect(
            url_for("upload")
        )

    # Read file
    file_data = uploaded_file.read()

    if not file_data:

        flash(
            "The selected file is empty."
        )

        return redirect(
            url_for("upload")
        )

    file_path = None

    try:

        # -------------------------------------------------
        # ENCRYPT FILE
        # -------------------------------------------------

        encrypted_data = cipher.encrypt(
            file_data
        )

        # -------------------------------------------------
        # UNIQUE STORED NAME
        # -------------------------------------------------

        stored_name = (
            str(session["user_id"])
            + "_"
            + os.urandom(8).hex()
            + ".enc"
        )

        # -------------------------------------------------
        # FULL PATH
        # -------------------------------------------------

        file_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            stored_name
        )

        # -------------------------------------------------
        # SAVE ENCRYPTED FILE
        # -------------------------------------------------

        with open(
            file_path,
            "wb"
        ) as encrypted_file:

            encrypted_file.write(
                encrypted_data
            )

        # -------------------------------------------------
        # SAVE DATABASE RECORD
        # -------------------------------------------------

        connection = get_db()

        try:

            connection.execute(
                """
                INSERT INTO files
                (
                    user_id,
                    original_name,
                    stored_name,
                    category
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    session["user_id"],
                    original_name,
                    stored_name,
                    category
                )
            )

            connection.commit()

        except Exception:

            connection.rollback()

            if (
                file_path
                and os.path.exists(file_path)
            ):

                os.remove(file_path)

            raise

        finally:

            connection.close()

        flash(
            "🔐 File encrypted and stored successfully!"
        )

        return redirect(
            url_for("vault")
        )

    except Exception as error:

        print(
            "UPLOAD ERROR:",
            error
        )

        flash(
            "Something went wrong while uploading."
        )

        return redirect(
            url_for("upload")
        )


# =========================================================
# DOWNLOAD
# =========================================================

@app.route("/download/<int:file_id>")
def download(file_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    connection = get_db()

    file_record = connection.execute(
        """
        SELECT *
        FROM files
        WHERE id = ?
        AND user_id = ?
        """,
        (
            file_id,
            session["user_id"]
        )
    ).fetchone()

    connection.close()

    if not file_record:

        flash(
            "File not found."
        )

        return redirect(
            url_for("vault")
        )

    encrypted_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        file_record["stored_name"]
    )

    if not os.path.exists(
        encrypted_path
    ):

        flash(
            "Encrypted file is missing."
        )

        return redirect(
            url_for("vault")
        )

    try:

        # Read encrypted file
        with open(
            encrypted_path,
            "rb"
        ) as encrypted_file:

            encrypted_data = encrypted_file.read()

        # Decrypt
        decrypted_data = cipher.decrypt(
            encrypted_data
        )

        # Send original file
        return send_file(
            BytesIO(decrypted_data),
            as_attachment=True,
            download_name=file_record["original_name"]
        )

    except Exception as error:

        print(
            "DOWNLOAD ERROR:",
            error
        )

        flash(
            "Unable to decrypt the file."
        )

        return redirect(
            url_for("vault")
        )


# =========================================================
# MEMORIES
# =========================================================

@app.route("/memories")
def memories():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    return render_template(
        "memories.html",
        username=session["username"]
    )


# =========================================================
# PROFILE
# =========================================================

@app.route("/profile")
def profile():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    return render_template(
        "profile.html",
        username=session["username"]
    )


# =========================================================
# NOTES
# =========================================================

@app.route("/notes", methods=["GET", "POST"])
def notes():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    user_id = session["user_id"]

    # -----------------------------------------------------
    # SAVE NOTE
    # -----------------------------------------------------

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        content = request.form.get(
            "content",
            ""
        ).strip()

        if not title or not content:

            flash(
                "Please enter both title and note."
            )

            return redirect(
                url_for("notes")
            )

        connection = get_db()

        connection.execute(
            """
            INSERT INTO notes
            (
                user_id,
                title,
                content
            )
            VALUES (?, ?, ?)
            """,
            (
                user_id,
                title,
                content
            )
        )

        connection.commit()

        connection.close()

        flash(
            "📝 Note saved successfully!"
        )

        return redirect(
            url_for("notes")
        )

    # -----------------------------------------------------
    # GET NOTES
    # -----------------------------------------------------

    connection = get_db()

    notes_list = connection.execute(
        """
        SELECT *
        FROM notes
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,)
    ).fetchall()

    connection.close()

    return render_template(
        "notes.html",
        username=session["username"],
        notes=notes_list
    )


# =========================================================
# DELETE NOTE
# =========================================================

@app.route(
    "/delete_note/<int:note_id>",
    methods=["POST"]
)
def delete_note(note_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    connection = get_db()

    connection.execute(
        """
        DELETE FROM notes
        WHERE id = ?
        AND user_id = ?
        """,
        (
            note_id,
            session["user_id"]
        )
    )

    connection.commit()

    connection.close()

    flash(
        "Note deleted successfully."
    )

    return redirect(
        url_for("notes")
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "Logged out successfully."
    )

    return redirect(
        url_for("login")
    )


# =========================================================
# FILE TOO LARGE
# =========================================================

@app.errorhandler(413)
def file_too_large(error):

    flash(
        "File is too large. Maximum size is 50 MB."
    )

    return redirect(
        url_for("upload")
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )