from flask import Flask, render_template, request, redirect, url_for, session, flash
import io
import mysql.connector
from mysql.connector import Error
from flask import Flask, send_file
from werkzeug.security import generate_password_hash, check_password_hash


from flask import jsonify

app = Flask(__name__)
app.secret_key = 'altf4'  

@app.route('/')
def index():
    return render_template('index.html')



@app.route('/carrinho')
def carrinho():
    carrinho = session.get('carrinho', {})
    print("Carrinho:", carrinho)  # Verifique o conteúdo do carrinho

    produtos = []
    connection = get_database_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        for produto_id in carrinho:
            cursor.execute("SELECT * FROM PRODUTO WHERE ID_PRODUTO = %s", (produto_id,))
            produto = cursor.fetchone()
            if produto:
                produto['quantidade'] = int(carrinho[produto_id])  # Garanta que quantidade é um inteiro
                produtos.append(produto)
        cursor.close()
        connection.close()

    return render_template('carrinho.html', produtos=produtos)




@app.route('/roupas')
def roupas():
    connection = get_database_connection()
    if connection is None:
        return "Error connecting to database", 500

    cursor = connection.cursor(dictionary=True)
    
    # Fetch data from CLIENTE table
    cursor.execute("SELECT * FROM CLIENTE")
    clientes = cursor.fetchall()

    # Fetch data from PRODUTO table
    cursor.execute("SELECT * FROM PRODUTO")
    produtos = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('index.html', clientes=clientes, produtos=produtos)


@app.route('/adicionar_ao_carrinho/<int:produto_id>')
def adicionar_ao_carrinho(produto_id):
    carrinho = session.get('carrinho', {})
    if produto_id in carrinho:
        carrinho[produto_id] = int(carrinho[produto_id]) + 1  # Assegure que a quantidade é um inteiro
    else:
        carrinho[produto_id] = 1  # Adicione o produto ao carrinho com quantidade 1

    session['carrinho'] = carrinho
    return redirect(url_for('carrinho'))


@app.route('/upload')
def upload_form():
    return render_template('upload.html')

@app.route('/upload_imagem', methods=['POST'])
def upload_image():
    produto_id = request.form.get('produto_id')
    imagem = request.files.get('imagem')

    if not imagem or not produto_id:
        return "Imagem ou ID do produto não fornecido", 400

    try:
        # Conectar ao banco de dados
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Joao0105",
            database="ecomerce"
        )
        cursor = connection.cursor()

        # Ler a imagem como dados binários
        binary_data = imagem.read()

        # Atualizar a tabela PRODUTO com a nova imagem
        query = "UPDATE PRODUTO SET imagem = %s WHERE ID_PRODUTO = %s"
        cursor.execute(query, (binary_data, produto_id))

        connection.commit()
        cursor.close()
        connection.close()

        return redirect(url_for('upload_form'))  # Redireciona de volta para o formulário de upload
    except Error as e:
        print(f"Erro ao atualizar imagem: {e}")
        return f"Erro ao atualizar imagem: {e}", 500

@app.route('/imagem/<int:produto_id>')
def mostrar_imagem(produto_id):
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Joao0105",
            database="ecomerce"
        )
        cursor = connection.cursor()
        query = "SELECT imagem FROM PRODUTO WHERE ID_PRODUTO = %s"
        cursor.execute(query, (produto_id,))
        imagem = cursor.fetchone()
        cursor.close()
        connection.close()

        if imagem:
            return send_file(
                io.BytesIO(imagem[0]),
                mimetype='image/jpeg',  # Ajuste o tipo MIME conforme o formato da sua imagem
                as_attachment=False,  # Defina como False para exibir a imagem diretamente no navegador
                download_name='imagem.jpg'  # Use 'download_name' em vez de 'attachment_filename'
            )
        else:
            return "Imagem não encontrada", 404
    except Error as e:
        print(f"Erro ao recuperar imagem: {e}")
        return f"Erro ao recuperar imagem: {e}", 500
    
    
@app.route('/adicionar_produto', methods=['GET', 'POST'])
def adicionar_produto():
    if request.method == 'POST':
        marca = request.form['marca']
        valor = float(request.form['valor'])
        imagem = request.files['imagem'].read()
        qtd_estoque = int(request.form.get('qtd_estoque', 0))  # Define um valor padrão se não fornecido

        try:
            connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="Joao0105",
                database="ecomerce"
            )
            cursor = connection.cursor()
            query = "INSERT INTO PRODUTO (MARCA, VALOR_PROD, IMAGEM, QTD_ESTOQUE) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (marca, valor, imagem, qtd_estoque))
            connection.commit()
            cursor.close()
            connection.close()

            return redirect(url_for('index'))  # Redireciona para uma página após a inserção
        except Error as e:
            print(f"Erro ao adicionar produto: {e}")
            return f"Erro ao adicionar produto: {e}", 500

    return render_template('adicionar_produto.html')
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['password']

        conn = get_database_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM CLIENTE WHERE EMAIL = %s', (email,))
        cliente = cursor.fetchone()
        cursor.close()
        conn.close()

        if cliente and check_password_hash(cliente['SENHA'], senha):
            session['user_id'] = cliente['ID_CLIENTE']
            flash('Login bem-sucedido!', 'success')
            return redirect(url_for('index'))  # Redireciona para a página principal ou dashboard
        else:
            flash('Email ou senha inválidos!', 'error')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        cpf = request.form['cpf']
        senha = request.form['password']
        senha_hash = generate_password_hash(senha)

        conn = get_database_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO CLIENTE (NOME, EMAIL, TELEFONE, CPF, SENHA) VALUES (%s, %s, %s, %s, %s)', 
                           (nome, email, telefone, cpf, senha_hash))
            conn.commit()
            flash('Registro bem-sucedido! Você pode fazer login agora.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            flash('Email ou CPF já registrado. Escolha outro.', 'error')
        finally:
            cursor.close()
            conn.close()

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Você saiu com sucesso!', 'success')
    return redirect(url_for('login'))


@app.route('/admin')
def admin():
    if 'user_id' in session and session.get('is_admin'):
        return render_template('adcionar_produto.html')
    flash('Acesso restrito!', 'error')
    return redirect(url_for('index'))
    

def get_database_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Joao0105",
            database="ecomerce"
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

if __name__ == '__main__':
    app.run(debug=True)
