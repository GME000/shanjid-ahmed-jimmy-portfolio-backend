from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from portfolio.models import (
    Category,
    Comment,
    ContactMessage,
    Education,
    Experience,
    Post,
    Project,
    Profile,
    Skill,
    Tag,
)


class Command(BaseCommand):
    help = "Create editable demo content for Shanjid Ahmed Jimmy"

    def handle(self, *args, **kwargs):
        user = get_user_model().objects.filter(is_superuser=True).first()
        if not user:
            self.stdout.write(self.style.WARNING("Create a superuser first."))
            return

        Profile.objects.update_or_create(
            pk=1,
            defaults={
                "full_name": "Shanjid Ahmed Jimmy",
                "headline": "Full-Stack Developer",
                "bio": "I build thoughtful digital products with Python, Django, React, and a strong bias toward learning by making. I enjoy turning complex requirements into clear, useful experiences and sharing what I learn along the way.",
                "email": user.email,
                "location": "Dhaka, Bangladesh",
                "github_url": "https://github.com/",
                "linkedin_url": "https://www.linkedin.com/",
                "years_of_experience": 1,
            },
        )

        skill_data = [
            ("Python", "BACKEND", 88), ("Django REST Framework", "BACKEND", 85),
            ("React", "FRONTEND", 86), ("JavaScript", "FRONTEND", 82),
            ("HTML & CSS", "FRONTEND", 90), ("SQLite", "DATABASE", 78),
            ("Git & GitHub", "TOOLS", 86), ("REST API Design", "BACKEND", 84),
            ("Responsive Design", "FRONTEND", 83), ("Problem Solving", "SOFT_SKILL", 92),
        ]
        skills = {}
        for order, (name, category, proficiency) in enumerate(skill_data):
            skills[name], _ = Skill.objects.update_or_create(
                name=name,
                defaults={"category": category, "proficiency": proficiency, "display_order": order, "is_featured": True},
            )

        Experience.objects.get_or_create(
            company="Independent Projects", role="Full-Stack Developer",
            defaults={"employment_type": "FREELANCE", "location": "Remote", "start_date": date(2024, 1, 1),
                      "is_current": True, "description": "Designing and building portfolio, API, and learning projects from idea to deployment."},
        )
        Experience.objects.get_or_create(
            company="Ostad", role="React + Django REST Framework Learner",
            defaults={"employment_type": "INTERNSHIP", "location": "Remote", "start_date": date(2025, 1, 1),
                      "end_date": date(2025, 6, 30), "description": "Built full-stack applications with authentication, CRUD workflows, validation, and responsive interfaces."},
        )
        Education.objects.get_or_create(
            institution="Ostad Learning Platform", degree="Professional Course",
            defaults={"field_of_study": "React and Django REST Framework", "start_year": 2025,
                      "description": "Practical full-stack development with modern frontend and backend tools."},
        )
        Education.objects.get_or_create(
            institution="Independent Study", degree="Continuous Learning",
            defaults={"field_of_study": "Web Development", "start_year": 2023,
                      "description": "Consistent practice through documentation, projects, and code review."},
        )

        for title, category, featured in [
            ("DevFolio Portfolio", "WEB", True), ("Learning Notes API", "API", True), ("Task Focus", "WEB", True),
        ]:
            project, _ = Project.objects.get_or_create(
                title=title,
                defaults={"summary": f"{title} — a focused project built with care.",
                          "description": "A practical project focused on clean interfaces, reliable data flows, and maintainable code. It reflects the lessons learned while building with React and Django REST Framework.",
                          "category": category, "github_url": "https://github.com/", "is_featured": featured,
                          "completed_date": date(2025, 6, 1)},
            )
            project.tech_stack.set([skills["Python"], skills["React"], skills["Git & GitHub"]])

        categories = [Category.objects.get_or_create(name=name)[0] for name in ("Development", "Learning", "Career")]
        tags = [Tag.objects.get_or_create(name=name)[0] for name in ("Python", "Django", "React", "APIs", "Career", "Lessons")]
        posts = [
            ("What I learned building my first DRF API", categories[0], "APIs"),
            ("Designing a portfolio that feels like mine", categories[1], "React"),
            ("Small habits that improved my coding", categories[2], "Lessons"),
            ("From requirements to a working product", categories[0], "Django"),
            ("Notes for the next iteration", categories[1], "Career"),
        ]
        for index, (title, category, tag_name) in enumerate(posts):
            post, _ = Post.objects.get_or_create(
                title=title,
                defaults={"excerpt": "A practical reflection from building this portfolio and its API.",
                          "content": ("Building software teaches you to make decisions deliberately. " * 55),
                          "category": category, "author": user,
                          "status": Post.DRAFT if index == 4 else Post.PUBLISHED,
                          "is_featured": index < 3},
            )
            post.tags.set([tags[0], tags[index + 1], Tag.objects.get(name=tag_name)])

        published = list(Post.objects.filter(status=Post.PUBLISHED)[:2])
        if published:
            Comment.objects.get_or_create(post=published[0], name="A curious reader", email="reader@example.com",
                                          defaults={"content": "This was a useful and clear explanation.", "is_approved": True})
            Comment.objects.get_or_create(post=published[0], name="Another reader", email="another@example.com",
                                          defaults={"content": "I am looking forward to trying this approach.", "is_approved": False})
            parent = Comment.objects.get_or_create(post=published[1], name="Project friend", email="friend@example.com",
                                                   defaults={"content": "The design direction feels very intentional.", "is_approved": True})[0]
            Comment.objects.get_or_create(post=published[1], parent=parent, name="Shanjid", email=user.email,
                                          defaults={"content": "Thank you — that was exactly the goal.", "is_approved": True})
        ContactMessage.objects.get_or_create(name="Demo visitor", email="visitor@example.com", subject="Hello",
                                             defaults={"message": "I enjoyed reading your portfolio and wanted to say hello."})
        ContactMessage.objects.get_or_create(name="Unread visitor", email="new@example.com", subject="Collaboration",
                                             defaults={"message": "I would love to discuss a possible collaboration.", "is_read": False})
        self.stdout.write(self.style.SUCCESS("Demo content created for Shanjid Ahmed Jimmy."))
