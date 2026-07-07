import httpx
import asyncio

async def test_chat():
    token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJpSlJETkxVMlk4cjlndDBMelFrYVN3WUZaYmFJeFlOOGlJMXJXUWcxQ1E0In0.eyJleHAiOjE3ODI1NTY4NjUsImlhdCI6MTc4MjU1NjU2NSwianRpIjoib25ydHJvOjk4NjZjZjUxLTRkMDItYzFkNy1iNjdjLWRjMzA3MjA2YjVjZSIsImlzcyI6Imh0dHA6Ly9sb2NhbGhvc3Q6ODA4MC9yZWFsbXMvVGVsZWNvbUFnZW50IiwiYXVkIjpbIm5vYy1hZ2VudC1hcHAiLCJhY2NvdW50Il0sInN1YiI6ImNiZDlkOWIwLWI5MDMtNDVkMy1iNTAxLTViZjQ4MDBhZTM1OSIsInR5cCI6IkJlYXJlciIsImF6cCI6Im5vYy1hZ2VudC1hcHAiLCJzaWQiOiJPXzJDbmhqQ3dsZi1za1NIdURNOTlMZDEiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHA6Ly9sb2NhbGhvc3Q6MzAwMCJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJhZG1pbiIsInVtYV9hdXRob3JpemF0aW9uIiwiZGVmYXVsdC1yb2xlcy10ZWxlY29tYWdlbnQiLCJ0aWVyMSJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInNjb3BlIjoib3BlbmlkIHByb2ZpbGUgZW1haWwiLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsInJvbGVzIjpbIm9mZmxpbmVfYWNjZXNzIiwiYWRtaW4iLCJ1bWFfYXV0aG9yaXphdGlvbiIsImRlZmF1bHQtcm9sZXMtdGVsZWNvbWFnZW50IiwidGllcjEiXSwibmFtZSI6IkxvbmcgTmd1eWVuIiwicHJlZmVycmVkX3VzZXJuYW1lIjoibG9uZ19uZ3V5ZW4iLCJnaXZlbl9uYW1lIjoiTG9uZyIsImZhbWlseV9uYW1lIjoiTmd1eWVuIiwiZW1haWwiOiJsb25nMjAxMjIwMDVAZ21haWwuY29tIn0.sDLyArSax5SqcH-vihvaQvOkE-iSLIvGykrxgZx-SXJc8V5W6eJ8qYTkol3JF_6PFxzCBQjrWesZuuC7t1IYIuzCRJFn034JMXMVYGbB6Pq0zv-CRyknwcpFAhndKFVLaSIlfCk0ug3VqUjcN2bq7ADAYby5JTGXN-LgIeLlp0nwwSIH8Jat_Q50NCpdnArk8dqnC1Rd3FM4xsMSnUpEc4ijf-TrATRqfyIIqZ6teqB_GVVdxq02K04F7CQVtk2Pi9pd601B_dEN1rB8fXTHDT0nhfAJax9-toTcrnmXen6gGm5Axtvrjz3pBkZAIUjdb0pBHaoTPt6FAJhDi6oy2A"
    
    async with httpx.AsyncClient() as client:
        # First get sessions
        headers = {"Authorization": f"Bearer {token}"}
        res = await client.get("http://localhost:8000/api/v1/sessions/", headers=headers)
        sessions = res.json()
        if not sessions:
            print("No sessions found")
            return
            
        session_id = sessions[0]["id"]
        print("Using session:", session_id)
        
        # Now send chat message
        req_data = {"session_id": session_id, "message": "hello"}
        
        async with client.stream("POST", "http://localhost:8000/api/v1/chat/", json=req_data, headers=headers) as response:
            print("Status:", response.status_code)
            async for chunk in response.aiter_text():
                print("CHUNK:", repr(chunk))

if __name__ == "__main__":
    asyncio.run(test_chat())
