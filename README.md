# Account Orbit Insight Compass

Build a polished, minimal, single-page web application called **Account Intelligence**.

This is a take-home recruitment project for an Applied Scientist role. The application helps a B2B SaaS Account Executive identify which customer accounts need attention, prioritize them, and prepare for meetings.

**Architecture requirements**

- Use React, TypeScript, Vite and Tailwind CSS.
- This is the frontend of a larger project. A Python FastAPI backend will be added later in a `backend/` folder of the SAME GitHub repository.
- Do NOT generate a backend, database, authentication, Supabase integration, or Lovable Cloud functionality.
- The finished application will be served locally by FastAPI, with the React frontend served as static files.
- Keep the frontend independent of hosting and external services.
- Put all backend communication behind a small, clearly separated API client module.
- Use relative API endpoints (`/api/...`) so frontend and backend can eventually run on the same origin.
- For now, implement a mock API adapter that simulates backend responses. Make switching between mock mode and real HTTP API straightforward.
- Do not implement machine learning, real AI calls, or scoring algorithms. All scoring and insights are placeholders.

**Application layout**

A clean, professional SaaS dashboard with a light background, subtle borders, restrained use of color, and good whitespace. No unnecessary animations or complex navigation.

Single page with three sections:

**1. CSV upload**

At the top, create a drag-and-drop CSV upload area with a file-picker button.

After upload:
- Show filename and number of accounts.
- Display a processing indicator.
- Call `POST /api/score` with the CSV as multipart/form-data using field name `file`.
- Display an error message if uploading or parsing fails.
- Replacing the CSV should clear the previous account selection and results.

The CSV will contain account data with fields such as `account_id`, `account_name`, `current_revenue`, `days_to_next_renewal`, `ai_usage`, `nr_active_users`, `nr_licensed_seats`, and others.

It does NOT need a target column. The frontend must not require `revenue_end_of_quarter`.

**2. Prioritized account list**

Below the upload area, display a ranked list of accounts returned by the scoring API.

Each row should show:
- Account name
- Overall priority score (0–100)
- Primary attention signal, such as Churn Risk, Contraction Risk, Expansion Opportunity, Renewal Urgency or Adoption Concern
- Financial exposure or opportunity, when available

Include a sorting dropdown with:
- Overall priority (default, descending)
- Revenue at risk
- Expansion opportunity
- Urgency

Initially display only 5 accounts. Add a "Load 5 more" button. Sorting should apply to the full scored dataset, not only the currently visible rows.

Clicking an account selects it and opens its details. Highlight the selected row.

**3. Selected account details and AI brief**

Display account details in a panel beside the list on larger screens and below it on small screens.

The panel should show:
- Account name and main priority classification
- Current annual revenue, if available
- Overall priority score
- Optional probability estimates for churn, contraction, stability and expansion
- A short account summary (one paragraph)
- Key insights as bullet points
- Recommended actions as bullet points

The summary and insights come from `POST /api/insight`, called only when an account is selected.

While waiting, show an appropriate loading state. Also handle errors and missing information gracefully. Do not fabricate values for unavailable fields. Show "Insufficient data" where appropriate.

**API contracts**

`POST /api/score`

Request: CSV file in multipart/form-data, field name `file`.

Response:

```json
{
  "accounts": [
    {
      "account_id": "ACC-0001",
      "account_name": "Example Company",
      "current_revenue": 120000,
      "priority_score": 87,
      "primary_signal": "churn_risk",
      "revenue_at_risk": 45000,
      "expansion_opportunity": 10000,
      "urgency_score": 75,
      "signals": {
        "churn_probability": 0.35,
        "contraction_probability": 0.20,
        "stable_probability": 0.35,
        "expansion_probability": 0.10
      }
    }
  ]
}
```

Allow optional/null values where data is unavailable. Keep `signals` extensible without requiring frontend changes to the entire application.

`POST /api/insight`

Request:

```json
{"account_id": "ACC-0001"}
```

Response:

```json
{
  "summary": "This account shows signs of declining engagement and an approaching renewal.",
  "insights": [
    "Low license utilization suggests adoption challenges.",
    "Renewal is approaching.",
    "A substantial amount of annual revenue is exposed."
  ],
  "recommended_actions": [
    "Schedule a meeting with the account decision-maker.",
    "Discuss adoption obstacles and possible solutions."
  ]
}
```

**Mock functionality**

The app must be functional immediately without a running backend.

Implement a mock API module with the same interface as the real API client.

For mock scoring, parse the uploaded CSV in the browser and generate deterministic placeholder scores for every account. Do not always return the same five fake companies. The number of returned accounts should match the uploaded file.

Mock insights should be returned asynchronously for any selected account ID.

Keep mock implementation separate from the React components. The frontend should not know whether it is calling mock or real APIs.

**Additional requirements**

- No charts necessary.
- No extra pages or navigation.
- No user accounts, login, database or hosting integration.
- Responsive, modern design, with usability prioritized over decoration.
- Clear empty, loading, success and error states.
- Maintainable React components and TypeScript interfaces.
- Avoid unnecessary dependencies.
- All source code should be exportable to GitHub and usable in a standalone local application.

The objective is a complete, attractive, usable frontend that can later connect to an independent Python FastAPI backend without major UI changes.

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/bbaf55d2-2b2a-401f-8e9f-d14cbd794e30).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
