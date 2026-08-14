import uuid
from datetime import date
from typing import TypedDict
from django.core.management.base import BaseCommand
from core.models.cohort import Cohort
from core.models.student import Student
from core.models.curriculum import Topic, Problem
from core.models.choices import CohortStatusChoices, StudentStatusChoices, ProblemSourceChoices, ProblemDifficultyChoices


class Command(BaseCommand):
    help = "Seed real-world curriculum data for Year 1 (DSA) and Year 2 (System Design & Projects)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding curriculum data..."))

        # 1. Create or get Default Cohort
        cohort, _ = Cohort.objects.get_or_create(
            name="BigO Academy - Cohort 6",
            defaults={
                "status": CohortStatusChoices.ACTIVE,
                "start_date": date(2026, 1, 15),
                "expected_graduation_date": date(2027, 12, 20),
                "student_capacity": 60,
                "enrolled_student_count": 2,
            }
        )
        self.stdout.write(self.style.SUCCESS(f"Cohort ready: {cohort.name} ({cohort.id})"))

        # 2. Attach Students
        students_data = [
            ("b5bfc8ce-aea5-42ab-9d9e-e9d3be0fe7e6", "Test Student", "student@example.com"),
            ("f18eb754-ab79-4de3-8afa-d93dad6c764b", "Tsion Shimelis", "tsionshimelis900@gmail.com"),
        ]

        for u_id_str, name, email in students_data:
            u_id = uuid.UUID(u_id_str)
            student, created = Student.objects.get_or_create(
                user_id=u_id,
                defaults={
                    "full_name": name,
                    "email": email,
                    "cohort": cohort,
                    "year_phase": 1,
                    "status": StudentStatusChoices.ACTIVE,
                    "joined_at": date(2026, 1, 15),
                    "attendance_percentage": 95.0,
                }
            )
            if not created and student.cohort != cohort:
                student.cohort = cohort
                student.save()
            self.stdout.write(self.style.SUCCESS(f"Student linked to cohort: {student.full_name}"))

        # 3. Clean existing topics for this cohort to prevent duplicate seeding
        Problem.objects.filter(topic__cohort=cohort).delete()
        Topic.objects.filter(cohort=cohort).delete()

        # 4. Define Year 1 Topics (DSA & Problem Solving)
        ProblemTuple = tuple[str, ProblemSourceChoices, str, ProblemDifficultyChoices]

        class TopicDict(TypedDict):
            title: str
            description: str
            display_order: int
            problems: list[ProblemTuple]

        year_1_topics: list[TopicDict] = [
            {
                "title": "Arrays, Strings & Two Pointers",
                "description": "Master core array manipulations, sliding window, prefix sums, and two-pointer techniques for O(N) runtime.",
                "display_order": 1,
                "problems": [
                    ("Two Sum", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/two-sum/", ProblemDifficultyChoices.EASY),
                    ("3Sum", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/3sum/", ProblemDifficultyChoices.MEDIUM),
                    ("Container With Most Water", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/container-with-most-water/", ProblemDifficultyChoices.MEDIUM),
                    ("Minimum Size Subarray Sum", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/minimum-size-subarray-sum/", ProblemDifficultyChoices.MEDIUM),
                    ("Subarray Sum Equals K", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/subarray-sum-equals-k/", ProblemDifficultyChoices.MEDIUM),
                ]
            },
            {
                "title": "Recursion & Backtracking",
                "description": "Develop intuition for state space trees, decision branching, combinatorial generation, and prune optimization.",
                "display_order": 2,
                "problems": [
                    ("Subsets II", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/subsets-ii/", ProblemDifficultyChoices.MEDIUM),
                    ("Permutations", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/permutations/", ProblemDifficultyChoices.MEDIUM),
                    ("Word Search", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/word-search/", ProblemDifficultyChoices.MEDIUM),
                    ("N-Queens", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/n-queens/", ProblemDifficultyChoices.HARD),
                ]
            },
            {
                "title": "Stacks, Queues & Monotonic Sequences",
                "description": "Understand LIFO/FIFO mechanics, expression evaluation, monotonic stack patterns, and LRU cache structures.",
                "display_order": 3,
                "problems": [
                    ("Valid Parentheses", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/valid-parentheses/", ProblemDifficultyChoices.EASY),
                    ("Daily Temperatures", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/daily-temperatures/", ProblemDifficultyChoices.MEDIUM),
                    ("Sliding Window Maximum", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/sliding-window-maximum/", ProblemDifficultyChoices.HARD),
                    ("LRU Cache", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/lru-cache/", ProblemDifficultyChoices.MEDIUM),
                ]
            },
            {
                "title": "Binary Search & Search Space Optimization",
                "description": "Explore logarithmic searching on ordered arrays, rotated boundaries, and binary search on abstract solution spaces.",
                "display_order": 4,
                "problems": [
                    ("Binary Search", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/binary-search/", ProblemDifficultyChoices.EASY),
                    ("Search in Rotated Sorted Array", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/search-in-rotated-sorted-array/", ProblemDifficultyChoices.MEDIUM),
                    ("Koko Eating Bananas", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/koko-eating-bananas/", ProblemDifficultyChoices.MEDIUM),
                    ("Median of Two Sorted Arrays", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/median-of-two-sorted-arrays/", ProblemDifficultyChoices.HARD),
                ]
            },
            {
                "title": "Trees & Binary Search Trees (BST)",
                "description": "Hierarchical structures, BFS/DFS tree traversals, Lowest Common Ancestor, and BST invariants.",
                "display_order": 5,
                "problems": [
                    ("Maximum Depth of Binary Tree", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/maximum-depth-of-binary-tree/", ProblemDifficultyChoices.EASY),
                    ("Lowest Common Ancestor of a Binary Tree", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/", ProblemDifficultyChoices.MEDIUM),
                    ("Serialize and Deserialize Binary Tree", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/serialize-and-deserialize-binary-tree/", ProblemDifficultyChoices.HARD),
                    ("Validate Binary Search Tree", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/validate-binary-search-tree/", ProblemDifficultyChoices.MEDIUM),
                ]
            },
            {
                "title": "Graphs: Traversals, TopoSort & Shortest Paths",
                "description": "Connected components, BFS shortest paths, Topological Sorting, Dijkstra's algorithm, and Disjoint Set Union (DSU).",
                "display_order": 6,
                "problems": [
                    ("Number of Islands", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/number-of-islands/", ProblemDifficultyChoices.MEDIUM),
                    ("Course Schedule II", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/course-schedule-ii/", ProblemDifficultyChoices.MEDIUM),
                    ("Network Delay Time", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/network-delay-time/", ProblemDifficultyChoices.MEDIUM),
                    ("Word Ladder", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/word-ladder/", ProblemDifficultyChoices.HARD),
                ]
            },
            {
                "title": "Dynamic Programming (1D & 2D)",
                "description": "Identify overlapping subproblems and optimal substructure. Master memoization, tabulation, knapsack, and sequence DP.",
                "display_order": 7,
                "problems": [
                    ("Climbing Stairs", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/climbing-stairs/", ProblemDifficultyChoices.EASY),
                    ("Coin Change", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/coin-change/", ProblemDifficultyChoices.MEDIUM),
                    ("Longest Common Subsequence", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/longest-common-subsequence/", ProblemDifficultyChoices.MEDIUM),
                    ("Edit Distance", ProblemSourceChoices.LEETCODE, "https://leetcode.com/problems/edit-distance/", ProblemDifficultyChoices.HARD),
                ]
            },
        ]

        # 5. Define Year 2 Topics (System Design & High-Scale Projects)
        year_2_topics: list[TopicDict] = [
            {
                "title": "System Design Fundamentals & API Architecture",
                "description": "Architect high-throughput REST & gRPC APIs, implement API Gateways, and design rate limiters (Token Bucket & Leaky Bucket).",
                "display_order": 8,
                "problems": [
                    ("Design a Scalable URL Shortener (TinyURL)", ProblemSourceChoices.LEETCODE, "https://github.com/donnemartin/system-design-primer#design-pastebin", ProblemDifficultyChoices.MEDIUM),
                    ("Design a Rate Limiter API (Token Bucket)", ProblemSourceChoices.CODEFORCES, "https://github.com/donnemartin/system-design-primer#design-a-rate-limiter", ProblemDifficultyChoices.HARD),
                    ("REST vs gRPC Microservice Protocol Benchmark", ProblemSourceChoices.LEETCODE, "https://grpc.io/docs/guides/", ProblemDifficultyChoices.MEDIUM),
                ]
            },
            {
                "title": "Scalable Database Architecture & Partitioning",
                "description": "SQL vs NoSQL trade-offs, B-Tree & LSM-Tree indexing, horizontal database sharding, and distributed ACID transactions.",
                "display_order": 9,
                "problems": [
                    ("B-Tree vs LSM-Tree Storage Engine Architecture", ProblemSourceChoices.CODEFORCES, "https://github.com/donnemartin/system-design-primer#database", ProblemDifficultyChoices.MEDIUM),
                    ("Horizontal Sharding & Consistent Hashing Design", ProblemSourceChoices.LEETCODE, "https://github.com/donnemartin/system-design-primer#consistent-hashing", ProblemDifficultyChoices.HARD),
                    ("Distributed ACID Transactions & 2PC Protocol", ProblemSourceChoices.LEETCODE, "https://microservices.io/patterns/data/database-per-service.html", ProblemDifficultyChoices.HARD),
                ]
            },
            {
                "title": "Caching Strategies & In-Memory Storage",
                "description": "Implement Redis Cache-Aside, Write-Through patterns, Cache Stampede protection, and CDN edge caching.",
                "display_order": 10,
                "problems": [
                    ("Redis Cache-Aside & Write-Through Architecture", ProblemSourceChoices.LEETCODE, "https://redis.io/docs/latest/develop/use/caching/", ProblemDifficultyChoices.MEDIUM),
                    ("CDN Content Delivery & Invalidation Strategies", ProblemSourceChoices.CODEFORCES, "https://github.com/donnemartin/system-design-primer#domain-name-system", ProblemDifficultyChoices.MEDIUM),
                ]
            },
            {
                "title": "Message Queues & Distributed Event Streams",
                "description": "Event-driven architecture with Apache Kafka, consumer group rebalancing, message partitioning, and idempotent event processing.",
                "display_order": 11,
                "problems": [
                    ("Kafka Event-Driven Order Processing Architecture", ProblemSourceChoices.LEETCODE, "https://kafka.apache.org/documentation/", ProblemDifficultyChoices.MEDIUM),
                    ("Idempotent Event Consumers & At-Least-Once Delivery", ProblemSourceChoices.CODEFORCES, "https://microservices.io/patterns/data/event-driven-architecture.html", ProblemDifficultyChoices.HARD),
                ]
            },
            {
                "title": "Microservices Design Patterns & Resiliency",
                "description": "Saga pattern for distributed transactions, Circuit Breakers (Resilience4j style), Service Mesh, and distributed tracing.",
                "display_order": 12,
                "problems": [
                    ("Saga Pattern Orchestration vs Choreography", ProblemSourceChoices.LEETCODE, "https://microservices.io/patterns/data/saga.html", ProblemDifficultyChoices.HARD),
                    ("Circuit Breaker & Fallback Policy Implementation", ProblemSourceChoices.CODEFORCES, "https://microservices.io/patterns/reliability/circuit-breaker.html", ProblemDifficultyChoices.MEDIUM),
                ]
            },
            {
                "title": "Capstone Project: Multi-Tenant LMS Microservice",
                "description": "Full-stack end-to-end design, implementation, containerization, and Kafka streaming deployment of the BigO Academy LMS Platform.",
                "display_order": 13,
                "problems": [
                    ("Full-Stack LMS System Architecture & Deployment", ProblemSourceChoices.LEETCODE, "https://github.com/donnemartin/system-design-primer", ProblemDifficultyChoices.HARD),
                    ("Kafka Live Progress Analytics Engine Integration", ProblemSourceChoices.CODEFORCES, "https://kafka.apache.org/intro", ProblemDifficultyChoices.HARD),
                ]
            },
        ]

        # 6. Create Topics and Problems
        for topic_info in year_1_topics:
            t = Topic.objects.create(
                cohort=cohort,
                title=topic_info["title"],
                description=topic_info["description"],
                year_phase=1,
                display_order=topic_info["display_order"],
                problem_count=len(topic_info["problems"]),
            )
            for p_title, p_source, p_url, p_diff in topic_info["problems"]:
                Problem.objects.create(
                    topic=t,
                    title=p_title,
                    source=p_source,
                    external_url=p_url,
                    difficulty=p_diff,
                )
            self.stdout.write(self.style.SUCCESS(f"  [Year 1] Seeded Topic: {t.title} ({len(topic_info['problems'])} problems)"))

        for topic_info in year_2_topics:
            t = Topic.objects.create(
                cohort=cohort,
                title=topic_info["title"],
                description=topic_info["description"],
                year_phase=2,
                display_order=topic_info["display_order"],
                problem_count=len(topic_info["problems"]),
            )
            for p_title, p_source, p_url, p_diff in topic_info["problems"]:
                Problem.objects.create(
                    topic=t,
                    title=p_title,
                    source=p_source,
                    external_url=p_url,
                    difficulty=p_diff,
                )
            self.stdout.write(self.style.SUCCESS(f"  [Year 2] Seeded Topic: {t.title} ({len(topic_info['problems'])} problems)"))

        self.stdout.write(self.style.SUCCESS("Curriculum successfully seeded!"))
