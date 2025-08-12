# Step-by-Step Service Exploration & Testing

## 1. **Preparation**

- Ensure Docker and Docker Compose are installed and running.
- Copy and edit your `.env` file:
  ```bash
  cd bi_selfservice
  cp config.env.example .env
  # Edit .env with your DB credentials, OpenAI key, etc.
  ```

---

## 2. **Service-by-Service Bring-up and Testing**

### **A. Redis Service**

**Start Redis only:**
```bash
docker compose up -d redis
```

**Test Redis:**
```bash
docker compose exec redis redis-cli ping
# Should return: PONG
```

---

### **B. PostgreSQL Database Connection**

> **Note:** Your chatbot connects to your existing on-premise PostgreSQL.  
> Make sure the database is running and accessible from the Docker network.

**Test DB Connection from Host:**
```bash
psql $DATABASE_URL
# Or use DBeaver, DataGrip, etc. to connect and browse tables
```

**Test DB Connection from a Container:**
```bash
docker run -it --rm --network=bi_staging_traefik postgres:15-alpine psql $DATABASE_URL              
```

---

### **C. Chatbot API Backend**

**Build and Start API Only:**
```bash
docker compose up -d chatbot-api
```

**Check Logs:**
```bash
docker compose logs -f chatbot-api
```

**Test API Health:**
```bash
curl http://localhost:8000/health
# Should return JSON with status: healthy
```

**Test API Docs:**
- Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser.
- Try the `/api/v1/chat/query` endpoint with a sample message:
  ```json
  {
    "message": "Show me user leads for last month"
  }
  ```

**Test DB/Redis Integration:**
- Try `/api/v1/chat/schema` to see if it returns your schema info.
- Try `/api/v1/health/detailed` for a full component check.

---

### **D. Web Interface**

**Build and Start Web Only:**
```bash
docker compose up -d chatbot-web
```

**Test Web UI:**
- Open [http://localhost:8080](http://localhost:8080)
- You should see the chat interface.
- Try sending a message (it will fail if API isn’t up, which is expected at this stage).

---

### **E. Nginx Reverse Proxy**

**Start Nginx Only:**
```bash
docker compose up -d nginx
```

**Test Nginx Routing:**
- Open [http://localhost:8080](http://localhost:8080) (should serve the web UI)
- Open [http://localhost:8080/api/v1/health](http://localhost:8080/api/v1/health) (should proxy to API health endpoint)

---

### **F. Full Stack Integration**

**Start All Services:**
```bash
docker-compose up -d
```

**Check All Logs:**
```bash
docker-compose logs -f
```

**Test End-to-End:**
- Open the web UI, ask a question, and verify you get a response.
- Try exporting results, browsing schema, and using quick actions.

---

## 3. **Troubleshooting Tips**

- **Service not starting?**  
  Check logs: `docker-compose logs <service>`
- **API errors?**  
  - Check DB credentials in `.env`
  - Check OpenAI API key
  - Try hitting `/api/v1/health/detailed`
- **Web UI blank?**  
  - Check Nginx logs
  - Check that `chatbot-web` and `nginx` are both running

---

## 4. **Iterative Development**

- Make code changes, then rebuild the affected service:
  ```bash
  docker-compose build chatbot-api
  docker-compose up -d chatbot-api
  ```
- For static web changes, just refresh the browser after editing files in `web/`.

---

## 5. **Cleanup**

- Stop all services:
  ```bash
  docker-compose down
  ```

---

## 6. **Advanced: Manual API Testing**

- Use Postman or `curl` to test endpoints directly.
- Example:
  ```bash
  curl -X POST http://localhost:8000/api/v1/chat/query \
    -H 'Content-Type: application/json' \
    -d '{"message": "Top 10 projects by leads"}'
  ```

---

## 7. **Security & Production Notes**

- Change all default secrets and passwords.
- Use read-only DB users.
- Set up SSL/TLS for Nginx in production.
- Monitor logs and rate limits.

---

**Let me know if you want a Markdown version of this for your docs, or if you want to automate any of these checks!**