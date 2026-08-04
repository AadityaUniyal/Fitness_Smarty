
import os
try:
    from google import genai
    _USE_GENAI_CLIENT = True
except ImportError:
    import google.generativeai as genai
    _USE_GENAI_CLIENT = False
from sqlalchemy.orm import Session
from sqlalchemy import text
import json


class AIAnalyst:
    """
    Translates natural language questions into SQL queries and executes them.
    """
    def __init__(self, db: Session):
        self.db = db
        # Set up Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            if _USE_GENAI_CLIENT:
                self.model = genai.Client(api_key=api_key)
            else:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    async def process_query(self, user_query: str, user_id: int):
        if not self.model:
            return {"error": "Gemini API key not configured"}

        # Define schema context for the LLM
        schema_context = """
        Tables:
        - users (id, clerk_user_id, username, email, age, weight_kg,
                 height_cm, gender, activity_level, primary_goal)
        - meal_logs (id, user_id, meal_name, total_calories,
                     total_protein, total_carbs, total_fats, created_at)
        - workout_logs (id, user_id, workout_name, duration_minutes,
                        calories_burned, created_at)

        Rules:
        1. Only return the SQL query.
        2. Use user_id = :user_id for all queries to filter
           for the specific user.
        3. Only use SELECT statements.
        4. Target PostgreSQL syntax.
        """

        prompt = (
            f"Convert this natural language question into a PostgreSQL query:\n"
            f"Question: {user_query}\n\n"
            f"Schema Context:\n{schema_context}\n\n"
            f"SQL Query:"
        )

        try:
            if _USE_GENAI_CLIENT:
                response = self.model.models.generate_content(
                    model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
                    contents=prompt,
                )
            else:
                response = self.model.generate_content(prompt)
            sql_query = (
                response.text.strip()
                .replace("```sql", "")
                .replace("```", "")
            )
            
            # Execute query Safely
            import logging
            cleaned_query = sql_query.strip().upper()
            is_select_or_with = (
                cleaned_query.startswith("SELECT")
                or cleaned_query.startswith("WITH")
            )
            
            # Detect injection and destructive SQL patterns in any part of the query
            mutating_keywords = {"INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "REPLACE", "CREATE"}
            has_mutation = any(kw in cleaned_query.split() or f" {kw} " in cleaned_query or f"\n{kw} " in cleaned_query for kw in mutating_keywords)

            if not is_select_or_with or has_mutation or ";" in cleaned_query:
                logging.getLogger(__name__).error(
                    f"Blocked potential destructive query or multi-statement execution attempt: {sql_query}"
                )
                return {"error": "Blocked potential security violation in query execution. Only safe read-only single-statement SELECT/WITH queries are allowed."}

            result = self.db.execute(text(sql_query), {"user_id": user_id})
            columns = result.keys()
            data = [dict(zip(columns, row)) for row in result.fetchall()]
            
            # Summarize results using Gemini
            summary_prompt = (
                f"Summarize these data results for the user's question: "
                f"'{user_query}'\nData: {json.dumps(data, default=str)}\n"
                f"Summary:"
            )
            if _USE_GENAI_CLIENT:
                summary_response = self.model.models.generate_content(
                    model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
                    contents=summary_prompt,
                )
            else:
                summary_response = self.model.generate_content(summary_prompt)
            
            return {
                "query": sql_query,
                "data": data,
                "summary": summary_response.text.strip()
            }
        except Exception as e:
            return {
                "error": f"Failed to process query: {str(e)}",
                "partial_sql": (
                    sql_query if 'sql_query' in locals() else None
                ),
            }
