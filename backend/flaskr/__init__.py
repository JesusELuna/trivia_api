import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page-1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    return questions[start:end]


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET, POST, PATCH, DELETE, OPTIONS')
        return response

    @app.route('/categories')
    def get_categories():
        categories = Category.query.all()
        formatted_categories = [category.format() for category in categories]

        if len(formatted_categories) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'categories': formatted_categories
        })

    @app.route('/questions')
    def get_questions():

        selection = Question.query.all()
        questions = paginate_questions(request, selection)

        if len(questions) == 0:
            abort(404)

        categories = Category.query.all()
        formatted_categories = [category.format() for category in categories]

        return jsonify({
            'success': True,
            'questions': questions,
            'total_questions': len(selection),
            'categories': formatted_categories,
            'current_category': None
        })

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()

            if(question is None):
                abort(422)

            question.delete()
            return jsonify({
                'success': True,
                'deleted': question_id
            })

        except:
            abort(422)

    @app.route('/questions', methods=['POST'])
    def add_questions():
        body = request.get_json()
        question = body.get('question', None)
        answer = body.get('answer', None)
        difficulty = body.get('difficulty', None)
        category = body.get('category', None)

        try:
            question = Question(question, answer, category, difficulty)
            question.insert()

            return jsonify({
                'success': True,
                'created': question.id,
            })
        except:
            abort(422)

    @app.route('/questions/search', methods=['POST'])
    def search_question():
        body = request.get_json()
        search_term = body.get('searchTerm', None)
        print(search_term)
        search = "%{}%".format(search_term)
        questions = Question.query.filter(
            Question.question.ilike(search)).all()

        formatted_questions = [question.format() for question in questions]

        return jsonify({
            'success': True,
            'questions': formatted_questions,
            'total_questions': len(formatted_questions)
        })

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_questions_by_category(category_id):

        questions = Question.query.filter(
            Question.category == category_id).all()

        if(questions is None):
            abort(404)

        formatted_questions = [question.format() for question in questions]

        return jsonify({
            'success': True,
            'questions': formatted_questions,
            'total_questions': len(formatted_questions)
        })

    @app.route('/quizzes', methods=['POST'])
    def quiz():
        try:
            body = request.get_json()
            quiz_category = body.get('quiz_category', None)
            previous_questions = body.get('previous_questions', None)

            questions = Question.query.filter(~Question.id.in_(previous_questions)).all() \
                if quiz_category['id'] == 0 \
                else Question.query.filter(
                ~Question.id.in_(previous_questions),
                Question.category == quiz_category['id']).all()
            question = None
            if(questions):
                question = random.choice(questions).format()
            return jsonify({
                'success': True,
                'question': question
            })
        except:
            abort(422)

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'resource not found'
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': 'unprocessable'
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 400,
            'message': 'bad request'
        }), 400

    return app
