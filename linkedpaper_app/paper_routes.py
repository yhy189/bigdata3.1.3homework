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


@paper_routes.route('/mainpage', methods=['GET'])
def mainpage():
    username = session.get('username')
    role = session.get('role')

    available_categories = ['cs.AI', 'cs.AR', 'cs.CC', 'cs.CE', 'cs.CG', 'cs.CL', 'cs.CR', 'cs.CV', 'cs.CY',
                            'cs.DB', 'cs.DC', 'cs.DL', 'cs.DM', 'cs.DS', 'cs.ET', 'cs.FL', 'cs.GL', 'cs.GR',
                            'cs.GT', 'cs.HC', 'cs.IR', 'cs.IT', 'cs.LG', 'cs.LO', 'cs.MA', 'cs.MM', 'cs.MS',
                            'cs.NA', 'cs.NE', 'cs.NI', 'cs.OH', 'cs.OS', 'cs.PF', 'cs.PL', 'cs.RO', 'cs.SC',
                            'cs.SD', 'cs.SE', 'cs.SI', 'cs.SY']
    session['last_page'] = url_for('paper_routes.mainpage')
    #recommended_papers = Paper.query.order_by(Paper.frequency.desc()).limit(5).all()

    return render_template('mainpage.html',
                           username=username,
                           role=role,
                           available_categories=available_categories,
                           #recommended_papers=recommended_papers
                           )


@paper_routes.route('/paper/<int:paper_id>', methods=['GET'])
def view_paper(paper_id):
    paper = Paper.query.get_or_404(paper_id)

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


# def get_similar_papers(paper):
#     """计算与该论文相似的论文（基于TF-IDF和余弦相似度）"""
#     # 获取所有论文的标题和摘要
#     papers = Paper.query.all()
#     corpus = [p.title + " " + p.abstract for p in papers]
#
#     # 使用TF-IDF将文本转化为向量
#     vectorizer = TfidfVectorizer(stop_words='english')
#     tfidf_matrix = vectorizer.fit_transform(corpus)
#
#     # 获取当前论文的索引
#     paper_index = papers.index(paper)
#
#     # 计算当前论文与其他论文之间的余弦相似度
#     cosine_similarities = cosine_similarity(tfidf_matrix[paper_index], tfidf_matrix).flatten()
#
#     # 获取相似度最高的论文（除当前论文本身外）
#     similar_papers = []
#     for i in range(len(cosine_similarities)):
#         if i != paper_index and cosine_similarities[i] > 0.1:  # 相似度阈值
#             similar_paper = papers[i]
#             similar_papers.append({
#                 "id": similar_paper.id,
#                 "title": similar_paper.title,
#                 "year": similar_paper.year,
#                 "category": similar_paper.category
#             })
#
#     return similar_papers


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