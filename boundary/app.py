import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, render_template, request, redirect, url_for, session, flash
from entity.entities import init_db
from control.controllers import AuthController, UserAccountController, UserProfileController, FundraisingActivityController, DoneeController

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)
app.secret_key = "change-this-in-production"

ROLES = ["User Admin", "Fund Raiser", "Donee", "Platform Manager"]

@app.route("/", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        result = AuthController.login(
            username=request.form.get("username", "").strip(),
            password=request.form.get("password", ""),
            selected_role=request.form.get("role", ""),
        )
        if result["success"]:
            session["user_id"]  = result["data"]["id"]
            session["username"] = result["data"]["username"]
            session["role"]     = result["data"]["role"]
            return redirect(url_for("dashboard"))
        else:
            flash(result["message"], "error")

    return render_template("login.html", roles=ROLES)

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    role = session.get("role")
    if role == "User Admin":
        return redirect(url_for("ua_accounts"))
    elif role == "Fund Raiser":
        return redirect(url_for("fr_activities"))
    elif role == "Donee":
        return redirect(url_for("d_browse"))
    return f"Welcome {session['username']}! Role: {role} — more pages coming soon."

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

@app.route("/admin/accounts")
def ua_accounts():
    if "user_id" not in session or session["role"] != "User Admin":
        return redirect(url_for("login"))
    q = request.args.get("q", "").strip()
    result = UserAccountController.list_accounts(q or None)
    return render_template("ua_accounts.html",
                           accounts=result["data"], q=q)


@app.route("/admin/accounts/create", methods=["GET", "POST"])
def ua_account_create():
    if "user_id" not in session or session["role"] != "User Admin":
        return redirect(url_for("login"))
    if request.method == "POST":
        new_pw = request.form.get("password", "").strip()
        result = UserAccountController.create_account(
            username=request.form.get("username", ""),
            password=request.form.get("password", ""),
            role=request.form.get("role", ""),
        )
        if result["success"]:
            flash(result["message"], "success")
            return redirect(url_for("ua_accounts"))
        else:
            flash(result["message"], "error")
    return render_template("ua_account_form.html",
                           form=request.form if request.method == "POST" else {},
                           action="Create")


@app.route("/admin/accounts/<int:aid>/edit", methods=["GET", "POST"])
def ua_account_edit(aid):
    if "user_id" not in session or session["role"] != "User Admin":
        return redirect(url_for("login"))
    if request.method == "POST":
        new_pw = request.form.get("password", "").strip()
        result = UserAccountController.update_account(
            account_id=aid,
            username=request.form.get("username", ""),
            role=request.form.get("role", ""),
            new_password=new_pw if new_pw else None,
        )
        if result["success"]:
            flash(result["message"], "success")
            return redirect(url_for("ua_accounts"))
        else:
            flash(result["message"], "error")
            form_data = request.form
    else:
        view_result = UserAccountController.view_account(aid)
        if not view_result["success"]:
            flash(view_result["message"], "error")
            return redirect(url_for("ua_accounts"))
        form_data = view_result["data"]
    return render_template("ua_account_form.html",
                           form=form_data, action="Edit", account_id=aid)


@app.route("/admin/accounts/<int:aid>/suspend", methods=["POST"])
def ua_account_suspend(aid):
    if "user_id" not in session or session["role"] != "User Admin":
        return redirect(url_for("login"))
    result = UserAccountController.suspend_account(aid)
    flash(result["message"], "success" if result["success"] else "error")
    return redirect(url_for("ua_accounts"))

@app.route("/admin/accounts/<int:aid>")
def ua_account_view(aid):
    if "user_id" not in session or session["role"] != "User Admin":
        return redirect(url_for("login"))
    result = UserAccountController.view_account(aid)
    if not result["success"]:
        flash(result["message"], "error")
        return redirect(url_for("ua_accounts"))
    return render_template("ua_account_view.html", account=result["data"])

@app.route("/admin/profiles")
def ua_profiles():
    if "user_id" not in session or session["role"] != "User Admin":
        return redirect(url_for("login"))
    q = request.args.get("q", "").strip()
    result = UserProfileController.list_profiles(q or None)
    return render_template("ua_profiles.html", profiles=result["data"], q=q)


@app.route("/admin/profiles/<int:pid>")
def ua_profile_view(pid):
    if "user_id" not in session or session["role"] != "User Admin":
        return redirect(url_for("login"))
    result = UserProfileController.view_profile(pid)
    if not result["success"]:
        flash(result["message"], "error")
        return redirect(url_for("ua_profiles"))
    return render_template("ua_profile_view.html", profile=result["data"])


@app.route("/admin/profiles/create", methods=["GET", "POST"])
def ua_profile_create():
    if "user_id" not in session or session["role"] != "User Admin":
        return redirect(url_for("login"))
    if request.method == "POST":
        result = UserProfileController.create_profile(
            name=request.form.get("name", ""),
            role=request.form.get("role", ""),
            email=request.form.get("email", ""),
            contact=request.form.get("contact", ""),
        )
        if result["success"]:
            flash(result["message"], "success")
            return redirect(url_for("ua_profiles"))
        else:
            flash(result["message"], "error")
    return render_template("ua_profile_form.html",
                           form=request.form if request.method == "POST" else {},
                           action="Create")


@app.route("/admin/profiles/<int:pid>/edit", methods=["GET", "POST"])
def ua_profile_edit(pid):
    if "user_id" not in session or session["role"] != "User Admin":
        return redirect(url_for("login"))
    if request.method == "POST":
        result = UserProfileController.update_profile(
            profile_id=pid,
            name=request.form.get("name", ""),
            role=request.form.get("role", ""),
            email=request.form.get("email", ""),
            contact=request.form.get("contact", ""),
        )
        if result["success"]:
            flash(result["message"], "success")
            return redirect(url_for("ua_profiles"))
        else:
            flash(result["message"], "error")
            form_data = request.form
    else:
        view_result = UserProfileController.view_profile(pid)
        if not view_result["success"]:
            flash(view_result["message"], "error")
            return redirect(url_for("ua_profiles"))
        form_data = view_result["data"]
    return render_template("ua_profile_form.html",
                           form=form_data, action="Edit", profile_id=pid)


@app.route("/admin/profiles/<int:pid>/suspend", methods=["POST"])
def ua_profile_suspend(pid):
    if "user_id" not in session or session["role"] != "User Admin":
        return redirect(url_for("login"))
    result = UserProfileController.suspend_profile(pid)
    flash(result["message"], "success" if result["success"] else "error")
    return redirect(url_for("ua_profile_view", pid=pid))

@app.route("/fundraiser/activities")
def fr_activities():
    if "user_id" not in session or session["role"] != "Fund Raiser":
        return redirect(url_for("login"))
    q = request.args.get("q", "").strip()
    result = FundraisingActivityController.list_activities(session["user_id"], q or None)
    return render_template("fr_activities.html", activities=result["data"], q=q)


@app.route("/fundraiser/activities/<int:aid>")
def fr_activity_view(aid):
    if "user_id" not in session or session["role"] != "Fund Raiser":
        return redirect(url_for("login"))
    result = FundraisingActivityController.view_activity(aid, session["user_id"])
    if not result["success"]:
        flash(result["message"], "error")
        return redirect(url_for("fr_activities"))
    return render_template("fr_activity_view.html", activity=result["data"])


@app.route("/fundraiser/activities/create", methods=["GET", "POST"])
def fr_activity_create():
    if "user_id" not in session or session["role"] != "Fund Raiser":
        return redirect(url_for("login"))
    cats = FundraisingActivityController.get_categories()["data"]
    if request.method == "POST":
        result = FundraisingActivityController.create_activity(
            fundraiser_id=session["user_id"],
            title=request.form.get("title", ""),
            description=request.form.get("description", ""),
            target_amount_str=request.form.get("target_amount", ""),
            category_id=request.form.get("category_id", ""),
            deadline=request.form.get("deadline", ""),
        )
        if result["success"]:
            flash(result["message"], "success")
            return redirect(url_for("fr_activities"))
        else:
            flash(result["message"], "error")
    return render_template("fr_activity_form.html",
                           form=request.form if request.method == "POST" else {},
                           categories=cats, action="Create")


@app.route("/fundraiser/activities/<int:aid>/edit", methods=["GET", "POST"])
def fr_activity_edit(aid):
    if "user_id" not in session or session["role"] != "Fund Raiser":
        return redirect(url_for("login"))
    cats = FundraisingActivityController.get_categories()["data"]
    if request.method == "POST":
        result = FundraisingActivityController.update_activity(
            activity_id=aid,
            fundraiser_id=session["user_id"],
            title=request.form.get("title", ""),
            description=request.form.get("description", ""),
            target_amount_str=request.form.get("target_amount", ""),
            category_id=request.form.get("category_id", ""),
            deadline=request.form.get("deadline", ""),
        )
        if result["success"]:
            flash(result["message"], "success")
            return redirect(url_for("fr_activities"))
        else:
            flash(result["message"], "error")
            form_data = request.form
    else:
        view_result = FundraisingActivityController.view_activity(aid, session["user_id"])
        if not view_result["success"]:
            flash(view_result["message"], "error")
            return redirect(url_for("fr_activities"))
        form_data = view_result["data"]
    return render_template("fr_activity_form.html",
                           form=form_data, categories=cats,
                           action="Edit", activity_id=aid)


@app.route("/fundraiser/activities/<int:aid>/delete", methods=["POST"])
def fr_activity_delete(aid):
    if "user_id" not in session or session["role"] != "Fund Raiser":
        return redirect(url_for("login"))
    result = FundraisingActivityController.delete_activity(aid, session["user_id"])
    flash(result["message"], "success" if result["success"] else "error")
    return redirect(url_for("fr_activities"))

@app.route("/donee/browse")
def d_browse():
    if "user_id" not in session or session["role"] != "Donee":
        return redirect(url_for("login"))
    q = request.args.get("q", "").strip()
    result = DoneeController.browse_activities(q or None)
    fav_ids = DoneeController.get_favourite_ids(session["user_id"])
    return render_template("d_browse.html",
                           activities=result["data"], fav_ids=fav_ids, q=q)


@app.route("/donee/browse/<int:aid>")
def d_activity_view(aid):
    if "user_id" not in session or session["role"] != "Donee":
        return redirect(url_for("login"))
    result = DoneeController.view_activity(aid, session["user_id"])
    if not result["success"]:
        flash(result["message"], "error")
        return redirect(url_for("d_browse"))
    return render_template("d_activity_view.html", activity=result["data"])


@app.route("/donee/favourite/<int:aid>", methods=["POST"])
def d_toggle_favourite(aid):
    if "user_id" not in session or session["role"] != "Donee":
        return redirect(url_for("login"))
    result = DoneeController.toggle_favourite(session["user_id"], aid)
    flash(result["message"], "success" if result["success"] else "error")
    return redirect(request.referrer or url_for("d_browse"))


@app.route("/donee/favourites")
def d_favourites():
    if "user_id" not in session or session["role"] != "Donee":
        return redirect(url_for("login"))
    q = request.args.get("q", "").strip()
    result = DoneeController.get_favourites(session["user_id"], q or None)
    return render_template("d_favourites.html", activities=result["data"], q=q)


@app.route("/donee/history")
def d_history():
    if "user_id" not in session or session["role"] != "Donee":
        return redirect(url_for("login"))
    q = request.args.get("q", "").strip()
    result = DoneeController.browse_history(q or None)
    return render_template("d_history.html", activities=result["data"], q=q)


@app.route("/donee/history/<int:aid>")
def d_history_view(aid):
    if "user_id" not in session or session["role"] != "Donee":
        return redirect(url_for("login"))
    result = DoneeController.view_history(aid)
    if not result["success"]:
        flash(result["message"], "error")
        return redirect(url_for("d_history"))
    return render_template("d_history_view.html", activity=result["data"])

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)

