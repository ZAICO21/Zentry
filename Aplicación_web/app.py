from flask import Flask, render_template, request, redirect, url_for, session
from flask import jsonify
from flask_pymongo import PyMongo
from bson import ObjectId
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'zentry_dev_123'

# Conexión a MongoDBimport os
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")

mongo = PyMongo(app)

### --- USERS --- ###
@app.route('/users', methods=['GET'])
def get_users():
    users = mongo.db.users.find()
    return jsonify([{**u, '_id': str(u['_id'])} for u in users])

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    result = mongo.db.users.insert_one(data)
    return jsonify({'_id': str(result.inserted_id)})

@app.route('/users/<id>', methods=['PUT'])
def update_user(id):
    data = request.get_json()
    mongo.db.users.update_one({'_id': ObjectId(id)}, {'$set': data})
    return jsonify({'msg': 'Usuario actualizado'})

@app.route('/users/<id>', methods=['DELETE'])
def delete_user(id):
    mongo.db.users.delete_one({'_id': ObjectId(id)})
    return jsonify({'msg': 'Usuario eliminado'})


### --- POSTS --- ###
@app.route('/posts', methods=['GET'])
def get_posts():
    posts = mongo.db.posts.find()
    return jsonify([{**p, '_id': str(p['_id'])} for p in posts])

@app.route('/posts', methods=['POST'])
def create_post():
    data = request.get_json()
    result = mongo.db.posts.insert_one(data)
    return jsonify({'_id': str(result.inserted_id)})

@app.route('/posts/<id>', methods=['PUT'])
def update_post(id):
    data = request.get_json()
    mongo.db.posts.update_one({'_id': ObjectId(id)}, {'$set': data})
    return jsonify({'msg': 'Post actualizado'})

@app.route('/posts/<id>', methods=['DELETE'])
def delete_post(id):
    mongo.db.posts.delete_one({'_id': ObjectId(id)})
    return jsonify({'msg': 'Post eliminado'})


### --- COMMENTS --- ###
@app.route('/comments', methods=['GET'])
def get_comments():
    comments = mongo.db.comments.find()
    return jsonify([{**c, '_id': str(c['_id'])} for c in comments])

@app.route('/comments', methods=['POST'])
def create_comment():
    data = request.get_json()
    result = mongo.db.comments.insert_one(data)
    return jsonify({'_id': str(result.inserted_id)})

@app.route('/comments/<id>', methods=['PUT'])
def update_comment(id):
    data = request.get_json()
    mongo.db.comments.update_one({'_id': ObjectId(id)}, {'$set': data})
    return jsonify({'msg': 'Comentario actualizado'})

@app.route('/comments/<id>', methods=['DELETE'])
def delete_comment(id):
    mongo.db.comments.delete_one({'_id': ObjectId(id)})
    return jsonify({'msg': 'Comentario eliminado'})

# Login y sesión

@app.route("/login", methods=["GET", "POST"])
def login():
    message = ''
    if "correo" in session:
        return redirect(url_for("logged_in"))

    if request.method == "POST":
        correo = request.form.get("correo")  # El campo del formulario se sigue llamando "email"
        contraseña = request.form.get("password")

        user = mongo.db.users.find_one({"correo": correo})

        if user:
            if user.get("contraseña") == contraseña:
                session["correo"] = correo
                return redirect(url_for("logged_in"))
            else:
                message = "Contraseña incorrecta"
        else:
            message = "Correo no encontrado"

    return render_template("login.html", message=message)

@app.route("/logout", methods=["POST", "GET"])
def logout():
    session.pop("correo", None)
    return redirect(url_for("login"))

@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST':
        nombre_usuario = request.form.get('nombre_usuario')
        correo = request.form.get('correo')
        contraseña = request.form.get('contraseña')
        pais = request.form.get('pais')

        existing_user = mongo.db.users.find_one({'correo': correo})
        if existing_user:
            message = "El correo ya está registrado"
        else:
            # Contar usuarios existentes para crear ID incremental
            count = mongo.db.users.count_documents({})
            id_usuario = f"u{count + 1:02d}"

            # Insertar nuevo usuario
            mongo.db.users.insert_one({
                'id': id_usuario,
                'nombre_usuario': nombre_usuario,
                'correo': correo,
                'contraseña': contraseña,
                'pais': pais
            })
            return redirect(url_for('login'))

    return render_template('register.html', message=message)

@app.route("/logged_in", methods=["GET"])
def logged_in():
    if "correo" not in session:
        return redirect(url_for("login"))

    posts = list(mongo.db.posts.find())
    usuarios = {u["id"]: u["nombre_usuario"] for u in mongo.db.users.find()}
    
    for post in posts:
        post["_id"] = str(post["_id"])
        post["nombre_autor"] = usuarios.get(post.get("autor_id"), post.get("autor", "Desconocido"))
        post["id_post"] = post.get("id", "")  # lo usaremos para empatar con comments

        comentarios = list(mongo.db.comments.find({"post_id": post["id_post"]}))
        for c in comentarios:
            c["nombre_autor"] = usuarios.get(c.get("autor_id"), "Anónimo")
        post["comentarios"] = comentarios

    return render_template("logged_in.html", email=session["correo"], posts=posts)




@app.route("/posts/html", methods=["POST"])
def create_post_html():
    if "correo" not in session:
        return redirect(url_for("login"))

    contenido = request.form.get("contenido")
    mongo.db.posts.insert_one({"contenido": contenido, "autor": session["correo"]})
    return redirect(url_for("logged_in"))

@app.route("/comments/<post_object_id>", methods=["POST"])
def create_comment_html(post_object_id):
    if "correo" not in session:
        return redirect(url_for("login"))

    comentario = request.form.get("comentario")
    user = mongo.db.users.find_one({"correo": session["correo"]})
    post = mongo.db.posts.find_one({"_id": ObjectId(post_object_id)})

    if not user or not post:
        return redirect(url_for("logged_in"))

    mongo.db.comments.insert_one({
        "contenido": comentario,
        "autor_id": user["id"],
        "post_id": post.get("id", ""),  # Usamos el campo "id": "p01"
        "fecha": datetime.utcnow()
    })
    return redirect(url_for("logged_in"))




if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
