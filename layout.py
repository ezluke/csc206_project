#jinja header template
from jinja2 import Template
header_template = Template("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ title }}</title>
    <link rel="icon" type="image/x-icon" href="{{ favicon }}">
    <link rel="stylesheet" href="{{ stylesheet }}">
</head>
<body class="site">
<header>
    <nav class="navbar" role="navigation" aria-label="main navigation">
        <div class="navbar-brand">
            <a class="navbar-item" href="/">
                <img class="logo" src="/static/logo.png" alt="Car Retail Logo">
            </a>
        </div>
        <div class="navbar-start">
            <a href="/" class="navbar-item option">
                Home
            </a>
            <a href="/cars" class="navbar-item option">
                Cars
            </a>
            <a href="/parts" class="navbar-item option">
                Parts
            </a>
        </div>
        <div class="navbar-end">
            <div class="navbar-item">
                <input class="input" type="text" placeholder="Search Cars" />
            </div>
            <div class="navbar-item">
                <div class="buttons">
                    <a href="/register" class="button is-primary">
                        <strong>Sign up</strong>
                    </a>
                    <a href="/login" class="button is-light">
                        Log in
                    </a>
                </div>
            </div>
        </div>
    </nav>
</header>
    <main class="content site-content">{{ content }}</main>
<footer class="footer site-footer">
    <div class="content has-text-centered">
        <p>© 2025 Car Retail. All rights reserved.</p>
    </div>
</footer>
</body>
""")
