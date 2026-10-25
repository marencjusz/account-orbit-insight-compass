
EXTRACT_PROMPT = """
Extract structured fields from each B2B SaaS sales-call
summary as defined in the structured output model annotations.

For each account id you are given:
1. Call transcript summary.
2. Number of employees.
3. Number of licenced seats.
4. Number of active users.

Call transcript is your main data to extract intent and reason. The rest
of the data is only to support inference of number of seats at risk.

Return every account_id exactly once.

"""