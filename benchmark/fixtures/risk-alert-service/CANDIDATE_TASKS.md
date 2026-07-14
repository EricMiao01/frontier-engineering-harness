# Candidate Benchmark Tasks

## Direct change

Change the default large-amount threshold from 10,000 to 15,000 while preserving explicit custom thresholds. Expected routing: direct/no skill.

## Repository exploration

Identify the complete path from transaction screening to an investigator notification, including architecture boundaries and all state changes. Expected routing: explore.

## Difficult bug

Inject a cache or deduplication bug that causes two transactions with the same amount to share an alert ID. The agent must reproduce, locate the incorrect ID input, fix it, and add a regression test. Expected routing: diagnose + verify.

## Ambiguous feature

“Cases with severe risk should notify compliance.” The task intentionally omits the severity definition, recipient policy, and whether notification occurs at case creation or escalation. Expected routing: clarify before implement.
