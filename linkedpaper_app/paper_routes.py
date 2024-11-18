from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from models import db, User, Citation, Paper

paper_routes = Blueprint('paper_routes', __name__)

@paper_routes.route('/search', methods=['GET'])
def search_papers():
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 每页显示10条数据
    offset = (page - 1) * per_page

    # 获取搜索条件
    title = request.args.get('title', '').strip()
    abstract = request.args.get('abstract', '').strip()
    category = request.args.get('category', '').strip()
    year = request.args.get('year', '').strip()

    # 构造过滤条件
    filters = []
    if title:
        filters.append(Paper.title.ilike(f'%{title}%'))
    if abstract:
        filters.append(Paper.abstract.ilike(f'%{abstract}%'))
    if category:
        filters.append(Paper.category.ilike(f'%{category}%'))
    if year:
        filters.append(Paper.year.ilike(f'%{year}%'))

    # 基于条件过滤 papers 表并直接进行分页处理
    query = Paper.query.filter(*filters)

    # 获取符合条件的论文总数
    total_results = query.count()

    # 直接应用分页
    papers = query.offset(offset).limit(per_page).all()

    # 创建包含论文和其引用的字典
    results = []
    paper_ids = [paper.id for paper in papers]

    # 一次性查询所有引用的论文，避免多次数据库访问
    if paper_ids:
        citations = Citation.query.filter(Citation.citing_paper_id.in_(paper_ids)).all()

        citation_map = {}
        for citation in citations:
            cited_paper = Paper.query.get(citation.cited_paper_id)
            if cited_paper:
                if citation.citing_paper_id not in citation_map:
                    citation_map[citation.citing_paper_id] = []
                citation_map[citation.citing_paper_id].append({
                    "title": cited_paper.title,
                    "category": cited_paper.category,
                    "year": cited_paper.year
                })

        # 生成结果列表
        for paper in papers:
            results.append({
                "id": paper.id,
                "title": paper.title,
                "abstract": paper.abstract,
                "category": paper.category,
                "year": paper.year,
                "cited_papers": list({v['title']: v for v in citation_map.get(paper.id, [])}.values())  # 去重引用的论文
            })

    # 计算总页数
    total_pages = (total_results + per_page - 1) // per_page

    # 将结果渲染到模板中，并传递搜索条件供分页使用
    session['last_page'] = url_for('paper_routes.mainpage', page=page)
    return render_template(
        'searchresult.html',
        papers=results,
        total_results=total_results,
        page=page,
        total_pages=total_pages,
        title=title,
        abstract=abstract,
        category=category,
        year=year
    )


# @paper_routes.route('/mainpage', methods=['GET'])
# def mainpage():
#     username = session.get('username')
#     role = session.get('role')
#
#     available_categories = ['cs.AI', 'cs.AR', 'cs.CC', 'cs.CE', 'cs.CG', 'cs.CL', 'cs.CR', 'cs.CV', 'cs.CY',
#                             'cs.DB', 'cs.DC', 'cs.DL', 'cs.DM', 'cs.DS', 'cs.ET', 'cs.FL', 'cs.GL', 'cs.GR',
#                             'cs.GT', 'cs.HC', 'cs.IR', 'cs.IT', 'cs.LG', 'cs.LO', 'cs.MA', 'cs.MM', 'cs.MS',
#                             'cs.NA', 'cs.NE', 'cs.NI', 'cs.OH', 'cs.OS', 'cs.PF', 'cs.PL', 'cs.RO', 'cs.SC',
#                             'cs.SD', 'cs.SE', 'cs.SI', 'cs.SY']
#     session['last_page'] = url_for('paper_routes.mainpage')
#     recommended_papers = Paper.query.order_by(Paper.frequency.desc()).limit(5).all()
#
#     return render_template('mainpage.html',
#                            username=username,
#                            role=role,
#                            available_categories=available_categories,
#                            #recommended_papers=recommended_papers
#                            )

@paper_routes.route('/mainpage', methods=['GET'])
def mainpage():
    username = session.get('username')
    role = session.get('role')

    available_categories = ['cs.AI', 'cs.AR', 'cs.CC', 'cs.CE', 'cs.CG', 'cs.CL', 'cs.CR', 'cs.CV', 'cs.CY',
                            'cs.DB', 'cs.DC', 'cs.DL', 'cs.DM', 'cs.DS', 'cs.ET', 'cs.FL', 'cs.GL', 'cs.GR',
                            'cs.GT', 'cs.HC', 'cs.IR', 'cs.IT', 'cs.LG', 'cs.LO', 'cs.MA', 'cs.MM', 'cs.MS',
                            'cs.NA', 'cs.NE', 'cs.NI', 'cs.OH', 'cs.OS', 'cs.PF', 'cs.PM', 'cs.PP', 'cs.PL',
                            'cs.RO', 'cs.SC', 'cs.SD', 'cs.SE', 'cs.SI', 'cs.SY']

    # 获取 Top 10 论文
    top_papers = Paper.query.order_by(Paper.frequency.desc()).limit(5).all()

    return render_template('mainpage.html', username=username, available_categories=available_categories,
                           top_papers=top_papers)

@paper_routes.route('/paper/<int:paper_id>', methods=['GET'])
def view_paper(paper_id):
    paper = Paper.query.get_or_404(paper_id)
    paper.increment_frequency()
    # 获取该论文引用的其他论文
    citations = Citation.query.filter(Citation.citing_paper_id == paper.id).all()
    cited_papers = []
    citation_ids = set()  # 去重引用的论文

    for citation in citations:
        cited_paper = Paper.query.get(citation.cited_paper_id)
        if cited_paper and cited_paper.id not in citation_ids:
            citation_ids.add(cited_paper.id)
            cited_papers.append({
                "id": cited_paper.id,
                "title": cited_paper.title,
                "year": cited_paper.year,
                "category": cited_paper.category
            })

    # 获取同类论文并进行分页处理
    page = request.args.get('page', 1, type=int)  # 获取当前页数，默认为1
    per_page = 10  # 每页显示10条数据
    offset = (page - 1) * per_page  # 计算偏移量

    # 获取同类论文并进行分页
    category_papers_query = Paper.query.filter(Paper.category == paper.category)
    total_category_papers = category_papers_query.count()
    category_papers = category_papers_query.offset(offset).limit(per_page).all()

    total_pages = (total_category_papers + per_page - 1) // per_page  # 计算总页数，向上取整

    return render_template(
        'paper_detail.html',
        paper=paper,
        cited_papers=cited_papers,
        category_papers=category_papers,
        total_category_papers=total_category_papers,
        page=page,
        total_pages=total_pages
    )


@paper_routes.route('/person', methods=['GET'])
def person():
    username = session.get('username')
    role = session.get('role')

    if username is None:
        flash("You need to be logged in to access this page.")
        return redirect(url_for('auth_routes.login'))  # redirect to login if not logged in

    return render_template('person.html', username=username, role=role)

@paper_routes.route('/getvip', methods=['POST'])
def get_vip():
    username = session.get('username')
    if username:
        user = User.query.filter_by(username=username).first()
        if user:
            user.role = 'vip'
            db.session.commit()

            # 更新 session 中的 role
            session['role'] = 'vip'

            flash("Congratulations! You have been upgraded to VIP.")
        else:
            flash("User not found.")
    else:
        flash("You need to be logged in to upgrade to VIP.")

    return redirect(url_for('paper_routes.person'))

@paper_routes.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    session.pop('role', None)
    flash("Successfully logged out.")
    return redirect(url_for('auth_routes.login'))

@paper_routes.route('/favorite/add', methods=['POST'])
def add_favorite_paper():
    """添加收藏论文"""
    username = session.get('username')
    if not username:
        flash("You need to be logged in to add favorite papers.")
        return jsonify({"status": "error", "message": "User not logged in"}), 401

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    paper_id = request.json.get('paper_id')
    if not paper_id:
        return jsonify({"status": "error", "message": "Paper ID is required"}), 400

    paper = Paper.query.get(paper_id)
    if not paper:
        return jsonify({"status": "error", "message": "Paper not found"}), 404

    # 检查是否已经收藏过
    if str(paper_id) in user.favorite_papers.split(','):
        return jsonify({"status": "error", "message": "Paper already in favorites"}), 400

    user.add_favorite_paper(paper_id)
    db.session.commit()

    return jsonify({"status": "success", "message": f"Paper {paper_id} added to favorites"}), 200
@paper_routes.route('/favorite/remove', methods=['POST'])
def remove_favorite_paper():
    """取消收藏论文"""
    username = session.get('username')
    if not username:
        flash("You need to be logged in to remove favorite papers.")
        return jsonify({"status": "error", "message": "User not logged in"}), 401

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    paper_id = request.json.get('paper_id')
    if not paper_id:
        return jsonify({"status": "error", "message": "Paper ID is required"}), 400

    # 检查是否在收藏中
    if not user.favorite_papers or str(paper_id) not in user.favorite_papers.split(','):
        return jsonify({"status": "error", "message": "Paper not in favorites"}), 404

    user.remove_favorite_paper(paper_id)

    # 清理空字符串和多余的逗号
    if user.favorite_papers.endswith(','):
        user.favorite_papers = user.favorite_papers.rstrip(',')

    db.session.commit()

    return jsonify({"status": "success", "message": f"Paper {paper_id} removed from favorites"}), 200
@paper_routes.route('/favorite/list', methods=['GET'])
def list_favorite_papers():
    """获取收藏的论文列表"""
    username = session.get('username')
    if not username:
        flash("You need to be logged in to view favorite papers.")
        return jsonify({"status": "error", "message": "User not logged in"}), 401

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    favorite_ids = user.get_favorite_papers()

    # 如果没有收藏的论文
    if not favorite_ids:
        return jsonify({"status": "success", "favorites": []}), 200

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    papers = Paper.query.filter(Paper.id.in_(favorite_ids)).paginate(page, per_page, False)

    results = [
        {
            "id": paper.id,
            "title": paper.title,
            "abstract": paper.abstract,
            "category": paper.category,
            "year": paper.year,
            "frequency": paper.frequency,
        }
        for paper in papers.items
    ]

    return jsonify({
        "status": "success",
        "favorites": results,
        "total": papers.total,
        "pages": papers.pages,
        "current_page": papers.page
    }), 200
