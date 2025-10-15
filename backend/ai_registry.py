render@srv-d3knhc1r0fns73brljl0-f97549d9f-68zvw:~/project/src$ # sanity
curl -s https://lightsignal-backend.onrender.com/health

# debug info (shows detected intents and envs)
curl -s https://lightsignal-backend.onrender.com/debug | jq .

# list intents
curl -s https://lightsignal-backend.onrender.com/intents | jq .

# business profile
curl -s -X POST https://lightsignal-backend.onrender.com/api/intent \
  -H "Content-Type: application/json" \
  -d '{"intent":"business_profile","company_id":"demo","input":{}}' | jq .

# debt management
curl -s -X POST https://lightsignal-backend.onrender.com/api/intent \
  -H "Content-Type: application/json" \
  -d '{"intent":"debt_management","company_id":"demo","input":{"target_paydown_months":12}}' | jq .
{"ok":true}{
  "detail": "Not Found"
}
{
  "detail": "Not Found"
}
{
  "detail": "Unknown intent: business_profile"
}
{
  "detail": "Unknown intent: debt_management"
}
render@srv-d3knhc1r0fns73brljl0-f97549d9f-68zvw:~/project/src$ 
