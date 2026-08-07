"""Quick diagnostic test for the AI tutor endpoint"""
import asyncio
import sys
sys.path.insert(0, '.')

async def main():
    # 1. Check settings
    from app.core.config import settings
    print(f"GROQ_API_KEY loaded: {'Yes (' + settings.GROQ_API_KEY[:10] + '...)' if settings.GROQ_API_KEY else 'NO'}")
    print(f"OPENAI_API_KEY loaded: {'Yes' if settings.OPENAI_API_KEY else 'NO'}")
    print(f"MONGODB_URL: {settings.MONGODB_URL}")
    
    # 2. Check database
    from app.core.database import connect_to_mongo, get_db
    await connect_to_mongo()
    db = get_db()
    print(f"Database connected: {'Yes' if db is not None else 'NO'}")
    
    # 3. Check openai package
    try:
        import openai
        print(f"openai package version: {openai.__version__}")
    except Exception as e:
        print(f"openai import error: {e}")
    
    # 4. Quick Groq API test
    if settings.GROQ_API_KEY:
        try:
            import openai as _openai
            client = _openai.AsyncOpenAI(
                api_key=settings.GROQ_API_KEY,
                base_url="https://api.groq.com/openai/v1"
            )
            resp = await client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": "Say hello in one word"}],
                max_tokens=10,
            )
            print(f"Groq API test: SUCCESS — '{resp.choices[0].message.content}'")
        except Exception as e:
            print(f"Groq API test FAILED: {e}")

asyncio.run(main())
