# Platform for publishing posts and comments with HTML templates.

## Project description:

Platform for publishing posts and comments. It is possible to: create groups, make posts, subscribe to authors.

The project created using HTML templates.
Restriction and roles:
- view contect - everyone
- create content - authenticated users
- change content - content's author

## How to launch a project:

Clone the repository and switch to it using the command line:
```
git clone git@github.com:Artem-Ter/hw05_final.git

```
```
cd hw05_final
```
Create and activate virtual environment:
```
python3 -m venv env
```
```
source env/bin/activate
```
```
python3 -m pip install --upgrade pip
```

Install dependencies from a file requirements.txt:
```
pip install -r requirements.txt
```

Make migrations:
```
python3 manage.py makemigrations
```
```
python3 manage.py migrate
```

Run project:
```
python3 manage.py runserver
```
## Technologies used:

- Python;
- Django Framework;
- HTML;
- CSS.

## Project author
[Artem Tereschenko](https://github.com/Artem-Ter)
