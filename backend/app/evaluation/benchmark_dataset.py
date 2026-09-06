"""
EnterpriseDoc AI - Built-in Benchmark Evaluation Dataset
Curated enterprise scenarios covering Financial, Legal, Technical, and HR domains.
"""

BENCHMARK_SAMPLES = [
    {
        "id": "bench-1",
        "domain": "Financial Report",
        "question": "What was the total revenue growth in the third quarter and what was the primary driver?",
        "ground_truth": "Third-quarter revenue reached $48.2 million, representing a 24.5% year-over-year growth, driven primarily by enterprise SaaS subscription expansion.",
        "contexts": [
            "Financial Highlights Q3: Consolidated revenue reached $48.2 million, up 24.5% year-over-year. The strong momentum was driven primarily by an accelerated 38% increase in enterprise SaaS subscriptions.",
            "Operating expenses rose 12% to $29.4 million due to increased investments in R&D and engineering talent.",
            "Cash flow from operations remained positive at $11.8 million for the nine-month period ending September 30."
        ]
    },
    {
        "id": "bench-2",
        "domain": "Legal Contract",
        "question": "What is the limitation of liability under the Master Services Agreement?",
        "ground_truth": "Neither party's aggregate liability shall exceed the total fees paid or payable by Client in the twelve (12) months preceding the claim.",
        "contexts": [
            "Section 11. Limitation of Liability: Except for gross negligence or willful misconduct, neither party's aggregate liability arising under this Agreement shall exceed the total fees paid or payable by Client in the twelve (12) months preceding the incident giving rise to liability.",
            "Section 12. Governing Law: This Agreement shall be governed by and construed in accordance with the laws of the State of Delaware, without regard to conflicts of law principles."
        ]
    },
    {
        "id": "bench-3",
        "domain": "Technical Specification",
        "question": "What is the maximum allowed query latency and throughput threshold for the retrieval engine?",
        "ground_truth": "The retrieval engine must maintain p95 latency below 120 milliseconds under a concurrent load of 250 queries per second.",
        "contexts": [
            "Performance Service Level Objectives (SLOs): The hybrid retrieval pipeline is engineered to deliver p95 search latency under 120ms at 250 QPS peak concurrency.",
            "Vector embeddings are cached in memory using FAISS IndexFlatIP to eliminate disk I/O bottlenecks during hot-path similarity computations."
        ]
    },
    {
        "id": "bench-4",
        "domain": "Executive Policy",
        "question": "What is the remote work equipment stipend policy for full-time employees?",
        "ground_truth": "Full-time employees receive a one-time remote home office setup stipend of $1,500 and a recurring monthly internet reimbursement of $75.",
        "contexts": [
            "Section 4. Remote Work Policy: All eligible full-time staff members are entitled to a one-time setup reimbursement of up to $1,500 for ergonomic office furniture and monitors.",
            "Additionally, the company provides a monthly internet connectivity reimbursement stipend of $75 processed via payroll."
        ]
    },
    {
        "id": "bench-5",
        "domain": "Insufficient Context Scenario",
        "question": "What was the exact stock option strike price for the senior engineering director hired in 2021?",
        "ground_truth": "The provided documents do not contain sufficient information to answer this question.",
        "contexts": [
            "Company stock options are subject to a 4-year vesting schedule with a 1-year cliff as determined by the Compensation Committee.",
            "Senior directors report directly to the VP of Engineering and are evaluated annually."
        ]
    }
]
