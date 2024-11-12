from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
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

        # for paper in papers:
        #     paper.frequency += 1
        # db.session.commit()  # 提交更改

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
                    "cited_papers": citation_map.get(paper.id, [])  # 包含引用的其他论文的标题和类别
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