# n8n Workflows for AI Productivity Agent

This directory contains n8n workflow configurations for automation.

## Overview

The AI Productivity Agent integrates with n8n to automate:
1. **Daily Planner** - Morning routine automation
2. **Missed Task Handler** - Rescheduling notifications
3. **Weekly Report** - Performance analysis

---

## Workflow 1: Daily Morning Planner

### What it does:
- Triggers every morning at 8 AM
- Fetches pending tasks from the API
- Calls AI to generate prioritized daily plan
- Sends plan via email & WhatsApp

### Steps:

```
[Cron] → [API: Get Tasks] → [API: Generate Plan] → [Send Email] → [Send WhatsApp]
Every 8 AM  Fetch pending    Get AI priorities     Email plan     Notify phone
```

### Setup in n8n:

1. **Create new workflow** in n8n
2. **Add Cron node**
   - Expression: `0 8 * * *` (8 AM daily)
   - Timezone: Your timezone

3. **Add HTTP Request (GET tasks)**
   ```
   URL: http://localhost:8000/api/v1/tasks?status=pending
   Method: GET
   Authentication: None (for now)
   ```

4. **Add HTTP Request (Generate Plan)**
   ```
   URL: http://localhost:8000/api/v1/tasks/analyze/daily-plan
   Method: POST
   Headers: Content-Type: application/json
   Body: {} (empty JSON)
   ```

5. **Add Gmail/Email node**
   - To: your.email@gmail.com
   - Subject: `📋 Your Daily Plan - ${now.format('YYYY-MM-DD')}`
   - Body Template:
   ```
   Good morning! 🌅

   Here's your optimized daily plan:

   {{ $node.HTTPRequest_GeneratePlan.json.today_plan.join('\n') }}

   AI Insights:
   {{ $node.HTTPRequest_GeneratePlan.json.insights }}

   Start with the first task!
   ```

6. **Add Twilio or WhatsApp node** (optional)
   - Phone: Your number
   - Message: Same as email but shorter

### Testing:
- Save and activate workflow
- Click "Test" - it will run manually
- You should receive email immediately

---

## Workflow 2: Missed Task Reminder Handler

### What it does:
- Runs every 2 hours
- Checks for overdue incomplete tasks
- Sends reminder notifications
- Tracks reminder count to avoid spam

### Setup:

```
[Cron] → [API: Get Overdue] → [Filter: Not Too Many Reminders] → [Send Notification]
Every 2h   Fetch tasks      Only if count < 3                  SMS/Email
```

### n8n Configuration:

1. **Cron Node**
   - Expression: `0 */2 * * *` (every 2 hours)

2. **HTTP: Get Overdue Tasks**
   ```
   URL: http://localhost:8000/api/v1/tasks?status=pending
   Method: GET
   ```

3. **Function Node** (filter and format)
   ```javascript
   // Filter overdue tasks
   const now = new Date();
   const overdue = items.map(item => {
     const tasks = item.json;
     return tasks.filter(t => {
       const due = new Date(t.due_date);
       return due < now && t.reminders_sent < 3;
     });
   });
   
   return [overdue[0].map(t => ({ json: t }))];
   ```

4. **Twilio/SMS Node**
   - Phone: Your number
   - Message: `⏰ Reminder: You have an overdue task: "${task_title}"`

5. **HTTP: Update Reminder Count**
   - For each task, POST to `/api/v1/tasks/{task_id}` with `reminders_sent + 1`

---

## Workflow 3: Weekly Productivity Report

### What it does:
- Runs every Monday at 9 AM
- Analyzes weekly performance
- Generates AI insights
- Sends comprehensive report

### Setup:

```
[Cron] → [API: Get Stats] → [API: Weekly Report] → [Send Report Email]
Monday 9   Fetch metrics    Generate AI analysis   Schedule email
```

### n8n Configuration:

1. **Cron Node**
   - Expression: `0 9 * * 1` (Monday 9 AM)

2. **HTTP: Get Summary Stats**
   ```
   URL: http://localhost:8000/api/v1/tasks/stats/summary
   Method: GET
   ```

3. **HTTP: Generate Weekly Report**
   ```
   URL: http://localhost:8000/api/v1/tasks/analyze/weekly-report
   Method: POST
   ```

4. **Gmail Node**
   - Subject: `📊 Weekly Productivity Report - Week ${now.weekNumber()}`
   - Body:
   ```
   Hello! Here's your productivity analysis for this week:

   📈 Statistics:
   - Total Tasks: {{ $node.HTTPGetStats.json.total_tasks }}
   - Completed: {{ $node.HTTPGetStats.json.completed }}
   - Completion Rate: {{ $node.HTTPGetStats.json.completion_rate.toFixed(1) }}%

   🎯 AI Analysis:
   {{ $node.HTTPReport.json.ai_report.summary }}

   💪 Strengths:
   {{ $node.HTTPReport.json.ai_report.strengths.join('\n') }}

   📈 Areas to improve:
   {{ $node.HTTPReport.json.ai_report.areas_for_improvement.join('\n') }}

   ✅ Next steps:
   {{ $node.HTTPReport.json.ai_report.recommended_actions.join('\n') }}

   Keep pushing! 🚀
   ```

---

## Installation Steps in n8n

### 1. Setup n8n (if not installed)

```bash
# Using npm
npm install -g n8n

# Or using Docker
docker run -it --rm --name n8n -p 5678:5678 n8nio/n8n
```

### 2. Access n8n
- Open: http://localhost:5678
- Create account and login

### 3. Create Connections
- **Gmail**: Go to Settings → Credentials → New → Gmail
  - Use OAuth2 flow
- **Twilio** (optional): Settings → Credentials → New → Twilio
  - Add Account SID and Auth Token from Twilio

### 4. Import Workflows
- Copy paste each workflow JSON from this folder OR
- Manually recreate using steps above

### 5. Enable/Activate Workflows
- Each workflow has an "Activate" toggle
- Turn ON to enable automation

---

## Environment Setup

### Backend Running
Ensure FastAPI server is running:

```bash
cd backend
python -m uvicorn app.main:app --reload
```

### API Testing
Before setting up n8n, test your API:

```bash
# Test connection
curl http://localhost:8000/health

# Get tasks
curl http://localhost:8000/api/v1/tasks

# Generate plan (needs tasks to exist)
curl -X POST http://localhost:8000/api/v1/tasks/analyze/daily-plan
```

---

## Troubleshooting

### Issue: Workflow doesn't trigger
- Check cron expression syntax
- Verify n8n service is running
- Check "Active" toggle is ON

### Issue: API call fails
- Verify backend is running on `localhost:8000`
- Check firewall allows port 8000
- Test curl command manually

### Issue: Email not sending
- Verify Gmail credentials are correct
- Enable "Less secure apps" or use App Passwords
- Check spam/junk folder

### Issue: Too many notifications
- Adjust cron timing (reduce frequency)
- Add filters in Function nodes
- Limit reminders per task

---

## Advanced: Custom Notifications

### WhatsApp Integration (Twilio)
```
1. Get Twilio account (free trial)
2. Get WhatsApp-enabled number
3. Add Twilio credentials in n8n
4. Replace SMS node with WhatsApp
```

### Slack Integration
```
1. Create Slack app at api.slack.com
2. Get webhook URL
3. Use HTTP node to POST to Slack webhook
4. Format JSON for Slack messages
```

### Google Calendar Integration
```
1. Add Google Calendar node
2. Auto-create events for scheduled tasks
3. Sync completed tasks
```

---

## Performance Tips

1. **Schedule wisely**: Don't run workflows every minute
2. **Use filters**: Only process necessary data
3. **Cache results**: Store frequent queries
4. **Monitor execution**: Check n8n logs regularly
5. **Test first**: Use Test mode before activating

---

## Next Steps

1. ✅ Set up basic workflows (all 3)
2. ✅ Test each workflow manually
3. ✅ Enable email reminders
4. 🔄 Add calendar integration (advanced)
5. 🔄 Add Slack notifications (advanced)
6. 🔄 Create custom dashboard (advanced)

---

## Support

For issues or questions:
- n8n Docs: https://docs.n8n.io
- API Swagger: http://localhost:8000/docs
- Troubleshoot: Check n8n UI Execution tab
