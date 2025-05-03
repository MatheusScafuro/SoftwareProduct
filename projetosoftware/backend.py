from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from flask import flash
import mysql.connector
import bcrypt
import re   

app = Flask(__name__)
app.secret_key = 'matheus123'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Guiguimar51cio87@@'
app.config['MYSQL_DB'] = 'cadastro_usuarios'

conexao = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Guiguimar51cio87@@",
    database="cadastro_usuarios"
)

mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('index.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        data_nascimento = request.form['data_nascimento']
        email = request.form['email']
        senha = request.form['senha']

        cpf_pattern = r'^\d{3}\.\d{3}\.\d{3}-\d{2}$'
        if not re.match(cpf_pattern, cpf):
            return render_template("erro.html", mensagem="CPF inválido. Use o formato 000.000.000-00.", url=url_for("register"))

        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_pattern, email):
            return render_template("erro.html", mensagem="E-mail inválido. Insira um e-mail válido.", url=url_for("register"))

        cur = mysql.connection.cursor()

        cur.execute("SELECT * FROM usuarios WHERE cpf = %s OR email = %s", (cpf, email))
        usuario_existente = cur.fetchone()

        if usuario_existente:
            return render_template("erro.html", mensagem="Erro: CPF ou E-mail já cadastrados. Tente outro.", url=url_for("register"))

        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())

        cur.execute("INSERT INTO usuarios (nome, cpf, data_nascimento, email, senha) VALUES (%s, %s, %s, %s, %s)",
                    (nome, cpf, data_nascimento, email, senha_hash))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM usuarios WHERE email=%s", (email,))
        usuario = cur.fetchone()
        cur.close()

        if usuario and bcrypt.checkpw(senha.encode('utf-8'), usuario[5]):
            session['usuario'] = usuario[0]
            return redirect(url_for('dashboard'))
        else:
            return render_template("erro.html", mensagem="Usuário ou senha incorretos.", url=url_for("login"))

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()

    cur.execute("SELECT COUNT(*) FROM usuarios")
    total_usuarios = cur.fetchone()[0]

    cur.execute("SELECT nome FROM usuarios")
    usuarios = cur.fetchall()
    
    cur.close()

    return render_template('dashboard.html', total_usuarios=total_usuarios, usuarios=usuarios)


@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('index'))

@app.route('/editar_perfil', methods=['GET', 'POST'])
def editar_perfil():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    usuario_id = session['usuario']
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        novo_nome = request.form['nome']
        nova_data_nascimento = request.form['data_nascimento']
        novo_email = request.form['email']
        senha_atual = request.form['senha_atual']  # Nova entrada no formulário
        nova_senha = request.form['nova_senha']  

        # Verificar se o e-mail já está cadastrado para outro usuário
        cur.execute("SELECT id, senha FROM usuarios WHERE email = %s AND id != %s", (novo_email, usuario_id))
        usuario_existente = cur.fetchone()
        if usuario_existente:
            cur.close()
            flash("Erro: E-mail já cadastrado para outro usuário.", "danger")
            return redirect(url_for('editar_perfil'))

        # Atualizar nome e email
        cur.execute("""
            UPDATE usuarios SET nome = %s, data_nascimento = %s, email = %s WHERE id = %s
        """, (novo_nome, nova_data_nascimento, novo_email, usuario_id))

        # Se o usuário quiser mudar a senha, verificar a senha atual primeiro
        if nova_senha:
            cur.execute("SELECT senha FROM usuarios WHERE id = %s", (usuario_id,))
            senha_bd = cur.fetchone()[0]

            # Verifica se a senha atual está correta
            if not bcrypt.checkpw(senha_atual.encode('utf-8'), senha_bd):
                cur.close()
                flash("Erro: Senha atual incorreta.", "danger")
                return redirect(url_for('editar_perfil'))

            # Atualiza a senha se a senha atual estiver correta
            senha_hash = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt())
            cur.execute("UPDATE usuarios SET senha = %s WHERE id = %s", (senha_hash, usuario_id))

        mysql.connection.commit()
        cur.close()

        flash("Perfil atualizado com sucesso!", "success")
        return redirect(url_for('dashboard'))

    # Carregar dados do usuário
    cur.execute("SELECT nome, cpf, data_nascimento, email FROM usuarios WHERE id = %s", (usuario_id,))
    usuario = cur.fetchone()
    cur.close()

    return render_template('editar_perfil.html', usuario=usuario)


@app.route('/esqueci-senha', methods=['GET', 'POST'])
def esqueci_senha():
    if request.method == 'POST':
        email = request.form['email']
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()
        if usuario:
            return redirect(url_for('redefinir_senha', email=email))
        else:
            flash("E-mail não encontrado.")
    return render_template('esqueci_senha.html')

@app.route('/redefinir-senha', methods=['GET', 'POST'])
def redefinir_senha():
    email = request.args.get('email')
    if request.method == 'POST':
        nova_senha = request.form['nova_senha']
        nova_senha_hash = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt())
        cursor = conexao.cursor()
        cursor.execute("UPDATE usuarios SET senha = %s WHERE email = %s", (nova_senha_hash, email))
        conexao.commit()
        flash("Senha atualizada com sucesso. Faça login novamente.")
        return redirect(url_for('login'))
    return render_template('redefinir_senha.html', email=email)




@app.route('/remover_usuario', methods=['POST'])
def remover_usuario():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    cpf = request.form['cpf']
    senha = request.form['senha']

    cur = mysql.connection.cursor()
    
    cur.execute("SELECT senha FROM usuarios WHERE cpf = %s", (cpf,))
    usuario = cur.fetchone()

    if usuario:
        senha_hash = usuario[0]

        if bcrypt.checkpw(senha.encode('utf-8'), senha_hash):  
            cur.execute("DELETE FROM usuarios WHERE cpf = %s", (cpf,))
            mysql.connection.commit()
            flash("Usuário removido com sucesso!", "success")
        else:
            flash("Senha incorreta!", "danger")
    else:
        flash("CPF não encontrado!", "danger")

    cur.close()
    return redirect(url_for('dashboard'))




if __name__ == '__main__':
    app.run(debug=True)
