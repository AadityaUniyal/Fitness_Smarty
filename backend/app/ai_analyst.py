import json
import logging
import os
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.ai_multi_provider import ai_engine

logger = logging.getLogger(__name__)


class AIAnalyst:
    """
    Translates natural language questions into safe PostgreSQL queries and executes them.
    Powered by the Multi-Provider AI Engine (Groq / Gemini / OpenRouter).
    """
    def __init__(self, db: Session):
        self.db = db

    async def process_query(self, user_query: str, user_id: int):
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
        1. Only return the raw SQL query without commentary.
        2. Use user_id = :user_id for all queries to filter for the specific user.
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
            res = await ai_engine.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are an expert PostgreSQL database analyst. Generate only safe, valid SELECT queries.",
                temperature=0.1,
                max_tokens=250
            )
            raw_text = res.get("text", "")
            sql_query = (
                raw_text.strip()
                .replace("```sql", "")
                .replace("```", "")
                .strip()
            )

            # Safety validations
            cleaned_query = sql_query.strip().upper()
            is_select_or_with = (
                cleaned_query.startswith("SELECT")
                or cleaned_query.startswith("WITH")
            )

            mutating_keywords = {"INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "REPLACE", "CREATE"}
            has_mutation = any(kw in cleaned_query.split() or f" {kw} " in cleaned_query or f"\n{kw} " in cleaned_query for kw in mutating_keywords)

            if not is_select_or_with or has_mutation or ";" in cleaned_query:
                logger.error(
                    f"Blocked potential destructive query or multi-statement execution attempt: {sql_query}"
                )
                return {"error": "Blocked potential security violation in query execution. Only safe read-only single-statement SELECT/WITH queries are allowed."}

            result = self.db.execute(text(sql_query), {"user_id": user_id})
            columns = result.keys()
            data = [dict(zip(columns, row)) for row in result.fetchall()]

            # Summarize results
            summary_prompt = (
                f"Summarize these data results for the user's question: "
                f"'{user_query}'\nData: {json.dumps(data, default=str)}\n"
                f"Summary in 2 clear sentences:"
            )
            summary_res = await ai_engine.chat_completion(
                messages=[{"role": "user", "content": summary_prompt}],
                system_prompt="You are a fitness data analyst. Provide a brief 2-sentence summary of the database query results.",
                temperature=0.5,
                max_tokens=150
            )

            return {
                "query": sql_query,
                "data": data,
                "summary": summary_res.get("text", "Query executed successfully."),
                "provider": res.get("provider", "multi-provider")
            }
        except Exception as e:
            return {
                "error": f"Failed to process query: {str(e)}",
                "partial_sql": (
                    sql_query if 'sql_query' in locals() else None
                ),
            }
