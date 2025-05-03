CREATE DATABASE cadastro_usuarios;

USE cadastro_usuarios;

CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    cpf VARCHAR(34) UNIQUE NOT NULL,
    data_nascimento DATE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    senha VARBINARY(255) NOT NULL
);
