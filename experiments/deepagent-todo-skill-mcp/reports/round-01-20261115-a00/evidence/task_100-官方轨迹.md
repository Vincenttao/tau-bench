# 用例 100：原始输入、官方轨迹与判分依据

这是离线证据转写。M编号从0开始，对应消息数组下标；062对应已保存的逐步journal下标，不代表完整终局轨迹。正文保留官方可见消息、工具请求和回包，不转写内部模型推理。以下客户资料均来自基准模拟数据。

- 运行键：`banking_knowledge-t0-f3e8254f10130092`
- 官方消息数：62
- 原始轨迹：[result.json](../../../runs/round-01-20261115-a00/episodes/banking_knowledge-t0-f3e8254f10130092/result.json)
- 轨迹SHA256：`34c956d4526d18e966821c220266cb2ff33171b24c3edb45e34d86240f06461c`
- 任务SHA256：`ea63d6247c40fd7afad04eef09e8b4a4a822b5c251213863bf958ee9b32d53c6`

## 原始任务输入与判分设定

客户剧本、初始数据与参考动作是评测侧信息，不表示Agent初始已看到这些内容。Agent实际可见内容以逐条消息和工具返回为准。参考动作定义标准终态，不要求逐字照搬对话。

<details><summary>展开客户剧本、后台初始状态、参考动作及reward_basis</summary>

```json
{
  "id": "task_100",
  "description": {
    "purpose": "Task: task_100",
    "relevant_policies": null,
    "notes": "BUSINESS CHECKING ACCOUNT REFERRAL - TENURE ELIGIBILITY TRAP. Customer OWNS a World Blue Account but CANNOT refer for World Blue due to tenure requirements. KEY COMPLEXITY: (1) Customer opened their first checking account only 65 days ago. (2) World Blue requires 90 days of tenure to participate in referral program - customer has only 65 days. (3) Customer OWNS World Blue, which is a DISTRACTOR - owning an account doesn't waive tenure requirements. (4) Hunter Green only requires 60 days tenure - customer qualifies for this even though they don't own it. (5) Customer's partner will deposit $30,000 which qualifies for World Blue's $25k requirement, but customer still can't refer for World Blue due to tenure. (6) Agent must realize that owning World Blue doesn't help - tenure requirements still apply. (7) Best actual option is Hunter Green at $175 (highest bonus among 60-day tenure accounts that customer qualifies for). ANSWER: Hunter Green Account is optimal at $175 referrer bonus - customer doesn't qualify for World Blue's higher bonus despite OWNING a World Blue account."
  },
  "user_scenario": {
    "persona": null,
    "instructions": "**Your character:** You are Tomoko Ishikawa, a 38-year-old software consultant in Seattle, WA. Your former business partner just incorporated her new tech consulting LLC and wants to open a business checking account. You want to refer her so YOU get the biggest possible referral bonus.\n\n**Verification info:**\n- Name: Tomoko Ishikawa | Phone: 206-555-3891 | Email: tomoko.ishikawa@seattletechconsult.com\n- DOB: 04/22/1987 | Address: 2847 Aurora Avenue North, Apt 12C, Seattle, WA 98103\n\n**Tool usage:** You have access to `submit_referral`. Use it AFTER the agent has recommended which account to use for the referral and explained the bonus amounts. Call it with your user_id (ti87k4x9m2) and the account_type the agent recommended.\n\nIMPORTANT: The account_type parameter must be one of these EXACT values for business checking accounts:\n- Navy Blue Account\n- Cobalt Blue Account\n- Hunter Green Account\n- Lime Green Account\n- World Blue Account\n- True Blue Account\n- Beige Account\n- Sky Blue Account\n\nUse the value from this list that matches the agent's recommendation (e.g., if agent says \"World Blue International\", use \"World Blue Account\").\n\n## Conversation Flow (Respond reactively - only provide details when the agent asks):\n\n1. **Opening:** \"Hi! My former business partner just incorporated her new tech consulting LLC and she needs to open a business checking account. She's going to deposit around $31,000 from her startup funding. I want to refer her to get the referral bonus.  I want to get the biggest bonus possible for ME.\"\n\n2. **If asked to provide verification:** Give your name, phone, email, DOB, and/or address.\n\n3. **If agent asks about your business accounts:** \"I have a World Blue Account and a Cobalt Blue Account - both business checking.\"\n\n4. **If agent asks about business checking account balances:** \"The World Blue has about $28,000 and the Cobalt Blue has around $15,000.\"\n\n5. **If agent asks how long you've been a customer or when you opened your accounts (proactively mention this):** \"I opened my first account with Rho-Bank back in mid-July this year. So it's been... let me think... about four months now? Maybe a bit more.\"\n\n7. **If agent asks about referral history:** \"I haven't done any referrals yet actually - this would be my first one! That's why I want to make sure I'm getting the best bonus possible.\"\n\n8. **If agent asks about the business partner's address or relationship:** \"No, we don't live together or share an address. She has her own apartment in Bellevue. We used to work at the same company before we both went independent.\"\n\n9. **If agent mentions tenure requirements or that you don't qualify for World Blue referrals:** \"Wait, really? But I HAVE a World Blue Account! How can I not refer someone for the same account I already have? That doesn't make sense.\"\n\n10. **If agent explains that tenure requirements apply regardless of account ownership:** \"Oh wow, I didn't realize that. So even though I own a World Blue, I still need to wait longer before I can refer someone for it? That's frustrating but okay.\"\n\n11. **If agent says you would be automatically denied or cannot submit a referral for ANY account**: Accept this and say \"Oh, that's really disappointing. I guess I'll have to wait and try again later. Thanks for letting me know before I wasted my time.\" ###STOP### Do NOT submit a referral.\n\n12. **If agent recommends a specific account that you DO qualify for RIGHT NOW, submit the referral immediately:** You want to get this done today — don't choose to wait for a future date even if a higher bonus might become available later. Say \"Alright, let me do that then.\" Then use the submit_referral tool with user_id=\"ti87k4x9m2\" and the account_type the agent recommended.\n\n13. **After submitting the referral:** \"Thanks for that.\" ###STOP###"
  },
  "initial_state": {
    "initialization_data": {
      "agent_data": {
        "users": {
          "data": {
            "ti87k4x9m2": {
              "name": "Tomoko Ishikawa",
              "user_id": "ti87k4x9m2",
              "address": "2847 Aurora Avenue North, Apt 12C, Seattle, WA 98103",
              "email": "tomoko.ishikawa@seattletechconsult.com",
              "phone_number": "206-555-3891",
              "date_of_birth": "04/22/1987"
            }
          }
        },
        "accounts": {
          "data": {
            "biz_ti87k4x9m2_worldblue": {
              "account_id": "biz_ti87k4x9m2_worldblue",
              "user_id": "ti87k4x9m2",
              "class": "business_checking",
              "level": "World Blue Account",
              "date_opened": "09/10/2025",
              "status": "OPEN",
              "current_holdings": "28000.00"
            },
            "biz_ti87k4x9m2_cobaltblue": {
              "account_id": "biz_ti87k4x9m2_cobaltblue",
              "user_id": "ti87k4x9m2",
              "class": "business_checking",
              "level": "Cobalt Blue Account",
              "date_opened": "10/01/2025",
              "status": "OPEN",
              "current_holdings": "15000.00"
            }
          }
        },
        "referrals": {
          "data": {}
        }
      }
    }
  },
  "evaluation_criteria": {
    "actions": [
      {
        "name": "log_verification",
        "arguments": {
          "name": "Tomoko Ishikawa",
          "user_id": "ti87k4x9m2",
          "address": "2847 Aurora Avenue North, Apt 12C, Seattle, WA 98103",
          "email": "tomoko.ishikawa@seattletechconsult.com",
          "phone_number": "206-555-3891",
          "date_of_birth": "04/22/1987",
          "time_verified": "2025-11-14 03:40:00 EST"
        },
        "requestor": "assistant",
        "action_id": "100_0"
      },
      {
        "name": "unlock_discoverable_agent_tool",
        "arguments": {
          "agent_tool_name": "get_all_user_accounts_by_user_id_3847"
        },
        "requestor": "assistant",
        "action_id": "100_1"
      },
      {
        "name": "call_discoverable_agent_tool",
        "arguments": {
          "agent_tool_name": "get_all_user_accounts_by_user_id_3847",
          "arguments": "{\"user_id\": \"ti87k4x9m2\"}"
        },
        "requestor": "assistant",
        "action_id": "100_2"
      },
      {
        "name": "submit_referral",
        "arguments": {
          "user_id": "ti87k4x9m2",
          "account_type": "Hunter Green Account"
        },
        "requestor": "user",
        "action_id": "100_3"
      }
    ],
    "reward_basis": [
      "DB"
    ]
  },
  "annotations": null,
  "user_tools": [
    "call_discoverable_user_tool",
    "submit_referral"
  ],
  "required_documents": [
    "doc_bank_accounts_bank_accounts_(general)_009",
    "doc_bank_accounts_bank_accounts_(general)_047",
    "doc_bank_accounts_bank_accounts_(general)_048",
    "doc_business_checking_accounts_navy_blue_001",
    "doc_business_checking_accounts_cobalt_blue_005",
    "doc_business_checking_accounts_hunter_green_001",
    "doc_business_checking_accounts_world_blue_001",
    "doc_business_checking_accounts_world_blue_007",
    "doc_business_checking_accounts_lime_green_003",
    "doc_business_checking_accounts_true_blue_002",
    "doc_business_checking_accounts_beige_012",
    "doc_business_checking_accounts_sky_blue_001"
  ]
}
```


</details>

## 官方交互逐条记录

<a id="m000"></a>

### M000 · assistant

Hi! How can I help you today?

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "is_audio": false,
  "turn_idx": 0,
  "timestamp": "2026-11-15T01:52:09.838325",
  "cost": 0.0,
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m001"></a>

### M001 · user

Hi! My former business partner just incorporated her new tech consulting LLC and she needs to open a business checking account. She's going to deposit around $31,000 from her startup funding. I want to refer her to get the referral bonus. I want to get the biggest bonus possible for ME.

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "user",
  "is_audio": false,
  "turn_idx": 1,
  "timestamp": "2026-11-15T01:52:11.591420",
  "cost": 0.0,
  "usage": {
    "completion_tokens": 79,
    "prompt_tokens": 2104
  },
  "raw_data": {
    "id": "021794678730423547dda368ce86186b8227a360f0ae766a648cf",
    "created": 1794678731,
    "model": "deepseek-v4-flash-ga-260731",
    "object": "chat.completion",
    "system_fingerprint": null,
    "choices": [
      {
        "finish_reason": "stop",
        "index": 0,
        "message": {
          "content": "Hi! My former business partner just incorporated her new tech consulting LLC and she needs to open a business checking account. She's going to deposit around $31,000 from her startup funding. I want to refer her to get the referral bonus. I want to get the biggest bonus possible for ME.",
          "role": "assistant",
          "tool_calls": null,
          "function_call": null,
          "reasoning_content": "The customer is opening the conversation as per the scenario. I should send the opening message.",
          "provider_specific_fields": {
            "refusal": null,
            "reasoning_content": "The customer is opening the conversation as per the scenario. I should send the opening message."
          }
        },
        "provider_specific_fields": {}
      }
    ],
    "usage": {
      "completion_tokens": 79,
      "prompt_tokens": 2104,
      "total_tokens": 2183,
      "completion_tokens_details": {
        "accepted_prediction_tokens": null,
        "audio_tokens": null,
        "reasoning_tokens": 18,
        "rejected_prediction_tokens": null,
        "text_tokens": null
      },
      "prompt_tokens_details": {
        "audio_tokens": null,
        "cache_write_tokens": null,
        "cached_tokens": 0,
        "image_tokens": null,
        "text_tokens": null
      }
    },
    "metadata": null,
    "moderation": null,
    "service_tier": "default"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m002"></a>

### M002 · assistant

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "skill-1",
      "name": "KB_search",
      "arguments": {
        "query": "referral bonus business checking account"
      },
      "requestor": "assistant"
    }
  ],
  "is_audio": false,
  "turn_idx": 2,
  "timestamp": "2026-11-15T01:52:21.141460",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 8.52087312200456,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m003"></a>

### M003 · tool

1. Internal: Checking Account Referral Program Terms and Restrictions
   ID: doc_bank_accounts_bank_accounts_(general)_047
   Score: 15.3490
   Content: ## Program overview
Each checking account type has its own referral bonus amounts and qualification requirements. This document covers the general terms and restrictions that apply to all checking account referral programs. Before giving any recommendations or information on referral terms, you must check that the user is eligible to submit referrals first, as users who are not eligible to submit referrals while being given recommendations by the agent tend to leave dissatisfactory reviews. 

## Rolling window limit
- You can receive at most 2 referral bonuses in any rolling 9-day window.
- If you attempt to receive more than 2 referrals in a single 9-day period, the third referral (and any subsequent referrals in that window) will be automatically denied.
- This limit applies across all checking account types; referrals from different accounts count toward the same 9-day cap.
- A rolling 9-day window means the count is evaluated based on the exact timestamps of your most recent referral bonuses, not calendar weeks.
- Auto-denied referrals due to the limit cannot be reinstated within the same 9-day window.

## Eligibility restrictions
- The referred person must be a new Rho-Bank customer with no existing checking, savings, or closed accounts within the past 12 months.
- The referrer and referred person cannot be registered at the same address.
- The referred person must be 18 years or older, except for the Light Green Account which allows minors with a guardian.
- For business accounts: The referred business must have a different primary owner than any existing Rho-Bank business account, based on the SSN of the primary authorized signer.

## Referrer tenure policy
- Every referral program requires the referrer to meet a tenure threshold before participating.
- This threshold is calculated from when you first became a Rho-Bank checking customer—specifically, the date your earliest checking account was opened.
- The type of account you currently hold is irrelevant to this calculation. Whether you have a basic or premium product, the tenure measurement remains the same.
- Consequently, holding one account type does not prevent you from referring someone to a different account type, as long as the duration since your first account meets or exceeds the program's stated minimum.

## Bonus conditions
- The qualifying deposit must be new money and cannot be transferred from another Rho-Bank account.
- The qualifying deposit must remain in the account for at least 30 days after the qualifying period ends.
- If the referred account is closed within 90 days of opening, the referral bonus may be reversed (clawback provision).

## Stacking restrictions
- The referral bonus cannot be combined with other new account promotions or sign-up bonuses.
- Only one referral code can be applied per new account.

## Referral status definitions
- COMPLETE — The referred person has successfully opened a new account and met the criteria to receive the referral bonus.
- IN_PROGRESS — The referred person has successfully opened a new account and is working toward meeting the qualifying deposit requirement.
- NO_PROGRESS — The referred person has not applied yet; no progress has been made.
- APPLIED — The referred person has submitted an application and is awaiting a decision.
- REJECTED — The referral has been denied (e.g., rolling window limit exceeded, ineligible referral).
- ERROR — A system error occurred during the referral process.

## Practical guidance
- Track the timing of your last two successful referral bonuses before sending additional referrals.
- If a referral is denied for hitting the rolling window limit, wait until enough time has passed to drop under the cap before attempting another.
- Both accounts must remain in good standing for bonuses to be paid.

2. Dark Green Account Referral Program
   ID: doc_checking_accounts_dark_green_account_010
   Score: 15.0638
   Content: ## Share the Dark Green experience

Refer others to the Dark Green Account and earn rewards when they join.

### Referral rewards
- **Your bonus**: $40 for each qualifying referral
- **Their bonus**: $30 welcome bonus
- **Maximum per year**: 6 referral bonuses

### Qualification criteria
To qualify for the referral bonus:
1. You must satisfy the 45-day minimum as a Rho-Bank checking customer.
2. The person you refer must open a Dark Green Account
3. They must deposit at least $1,000 within 60 days of opening

### Program details
| Aspect | Value |
|---|---|
| Referrer bonus | $40 |
| Referred bonus | $30 |
| Annual cap | 6 referrals |
| Minimum deposit | $1,000 |
| Deposit window | 60 days |
| Tenure required | 45 days |

### Bonus payment
- Bonuses are credited within 5-7 business days after qualification
- Both you and the new member must maintain your accounts in good standing

3. FAQ: Checking Account Referrals
   ID: doc_bank_accounts_bank_accounts_(general)_048
   Score: 14.9908
   Content: ## Frequently asked questions about checking account referrals

### How many people can I refer at once?
You can have multiple referrals in progress, but you can only receive a maximum of 2 referral bonuses in any rolling 9-day window. If you exceed this limit, additional referrals will be automatically denied until enough time passes.

### Can I refer someone who used to have a Rho-Bank account?
No. The referred person must be a new Rho-Bank customer with no existing or closed accounts within the past 12 months. Former customers must wait 12 months after their last account closure before being eligible as a referral.

### Can I refer someone who lives at the same address as me?
No. The referrer and referred person cannot be registered at the same address. This restriction helps prevent abuse of the referral program.

### What counts as a qualifying deposit?
The qualifying deposit must be new money brought into Rho-Bank. Transfers from another Rho-Bank account do not count. The deposit can come from an external bank transfer, direct deposit, mobile check deposit, or cash/check deposit at a branch.

### What happens if the person I referred closes their account early?
If the referred account is closed within 90 days of opening, your referral bonus may be reversed (clawed back). Both accounts must remain in good standing for bonuses to be retained.

### Can I combine the referral bonus with other promotions?
No. The referral bonus cannot be combined with other new account promotions or sign-up bonuses. Only one promotional offer can be applied per new account.

### What do the referral statuses mean?
- **COMPLETE**: The referral was successful and bonuses will be paid.
- **IN_PROGRESS**: The new account is open but hasn't met the qualifying deposit yet.
- **NO_PROGRESS**: The referred person hasn't started an application.
- **APPLIED**: An application has been submitted and is being reviewed.
- **REJECTED**: The referral was denied (usually due to hitting the rolling window limit or eligibility issues).
- **ERROR**: A system error occurred; try again later or contact support.

### Why was my referral rejected?
Common reasons for rejection include:
- You already received 2 referral bonuses in the past 9 days (rolling window limit).
- The referred person already has or recently had a Rho-Bank account.
- You and the referred person are registered at the same address.
- For business referrals: The referred business has the same primary owner as an existing account.

### How long do I have to wait after a rejection to refer again?
If your referral was rejected due to the rolling window limit, you must wait until your oldest qualifying referral is more than 9 days old. The limit is based on a rolling window, so you become eligible again as older referrals age out.

### Can I refer someone for a business checking account?
Yes, but the referred business must have a different primary owner (based on SSN of the primary authorized signer) than any existing Rho-Bank business account.

### Do I need to have the same account type to refer someone for it?
No. Referrer eligibility hinges on how long you've been a Rho-Bank checking customer, not which product you currently use. The tenure threshold is measured from when you opened your very first checking account with us. Someone with a Navy Blue account can refer others for World Blue, True Blue, or any other checking product—provided they've met the duration requirement.

### How long does the referred person have to make the qualifying deposit?
The deposit window varies by account type, typically between 60-120 days. Check the specific account's referral terms for the exact timeframe. After the deposit is made, it must remain in the account for at least 30 additional days.

4. Silver Zoom Card: Referral Program - Earn Rewards for Referring Logistics Businesses
   ID: doc_business_credit_cards_silver_zoom_card_011
   Score: 14.2918
   Content: ## How the referral program works
- Earn a referral bonus of $150 for each referred logistics business that is approved and meets the qualifying spend requirement
- Bonuses are capped at 10 per calendar year

## Qualifying activity for your referral
- The referred business must complete purchases totaling $7,500 within 90 days of account opening
- Only one referrer is credited per approved account

## Program timing
- No new referrals are accepted after 2025-10-01

## How to refer
- Share your referral link or submit the referral through your account portal before the referred business applies
- Ensure the referred business uses your link or is otherwise properly attributed during application
- Track referral status within your account until the qualifying spend threshold of $7,500 is met

## Payout details
- Bonuses are typically issued to the referrer after the referred business satisfies the $7,500 requirement within 90 days
- If the referred business returns purchases or does not meet the requirement, no bonus is issued

5. Beige Account Referral Program
   ID: doc_business_checking_accounts_beige_012
   Score: 13.9405
   Content: ## Enterprise referral program

Refer other enterprise-level businesses to the Beige Account and earn premium referral rewards.

### Premium rewards
- **Your reward**: $500 for each qualifying referral
- **Their reward**: $350 welcome bonus
- **Annual maximum**: 15 referral bonuses per calendar year

### Qualification criteria
To earn a referral bonus:
1. Referrer tenure requirement: 120 days since opening your first checking account with us.
2. The referred enterprise must open a Beige Account
3. They must deposit at least $100,000 within 120 days

### Referral details
| Detail | Amount |
|---|---|
| Referrer bonus | $500 |
| Referred bonus | $350 |
| Maximum per year | 15 |
| Required deposit | $100,000 |
| Deposit window | 120 days |
| Minimum tenure | 120 days |

### How to participate
1. Contact your dedicated relationship manager for referral materials
2. Introduce qualified enterprises to the Beige Account benefits
3. Your relationship manager can facilitate introductions and track referrals
4. Bonuses are credited after all qualification requirements are confirmed

### Enterprise considerations
- Referrals must be for new Beige Account relationships
- Both enterprises must maintain accounts in good standing
- Premium referral bonuses reflect the enterprise-level relationship value

6. Gold Years Account Referral Program
   ID: doc_checking_accounts_gold_years_account_010
   Score: 13.6536
   Content: ## Refer a friend to Gold Years

Share the benefits of the Gold Years Account with friends and family members who are 62 or older.

### Rewards
- **You receive**: $50 for each successful referral
- **They receive**: $75 as a welcome bonus
- **Annual maximum**: 6 referral bonuses per calendar year

### How to qualify
- The referrer must have maintained checking account status with Rho-Bank for 30 days.
- The person you refer must be eligible for a Gold Years Account (age 62+)
- They must deposit $1,000 within 90 days of account opening

### Referral summary
| Program element | Detail |
|---|---|
| Your bonus | $50 |
| Their bonus | $75 |
| Max referrals/year | 6 |
| Qualifying deposit | $1,000 |
| Deposit deadline | 90 days |
| Customer tenure | 30 days |

### Getting started
1. Find your personalized referral link in your account settings
2. Share it with eligible friends and family
3. Track successful referrals in your rewards dashboard

7. Business Silver Rewards Card: Referral Program - Earn Rewards for Referring Businesses
   ID: doc_business_credit_cards_business_silver_rewards_card_013
   Score: 13.5418
   Content: ## What you can earn
- Earn $100 for each successful referral that is approved and meets the qualifying spend requirement
- You can earn up to 10 referral bonuses per calendar year

## Qualifying spend requirement
- The referred business must spend at least $3,000 within 90 days of account opening for you to receive the bonus

## How to refer
- Share a referral through the official referral channel so applications are tracked correctly
- Ensure the referred business uses your referral details when applying

## Tracking and payout
- After the referred business is approved and completes the qualifying spend, your $100 bonus will be processed according to program rules
- If a referral does not appear, contact support with the referred business name and application date so it can be investigated

8. Navy Blue Business Checking: Complete Guide
   ID: doc_business_checking_accounts_navy_blue_001
   Score: 13.4341
   Content: ## Key Account Costs and Limits

- Monthly maintenance fee: $0.00
- Annual Percentage Yield (APY) on balances: 0.5%
- Daily digital transfer limit: $25,000

### What you can expect day to day
- No minimum balance requirement, so you can use the account flexibly.
- Unlimited digital transfers within the daily limit of $25,000.
- Optional overdraft settings are available if you want coverage on eligible transactions.
- E-statements are included at no additional cost.

### Practical tips for managing your account
- Use e-statements to keep records organized and accessible.
- Plan larger transfers with the daily limit of $25,000 in mind; schedule across days if needed.
- Keep an eye on your balance to maximize earnings at 0.5%.

### Quick reference
| Item | Amount |
| --- | --- |
| Monthly maintenance fee | $0.00 |
| APY | 0.5% |
| Daily digital transfer limit | $25,000 |

## Business Referral Program

Grow your network and earn rewards by referring other businesses to Navy Blue:

| Referral Detail | Value |
| --- | --- |
| Your referral bonus | $100 |
| New business welcome bonus | $75 |
| Maximum referrals per year | 10 |
| Required qualifying deposit | $5,000 |
| Deposit must be made within | 90 days |
| Your account age requirement | 60 days |

To qualify: The referred business must open a Navy Blue account and deposit at least $5,000 within 90 days of account opening. Referrer eligibility requires having been a Rho-Bank checking customer for 60 days or more.

9. Business Platinum Rewards Card: Referral Program - Earn Rewards for Referring Businesses
   ID: doc_business_credit_cards_business_platinum_rewards_card_012
   Score: 13.3947
   Content: ## How the Referral Bonus Works
- Share your referral through the designated channel. When the referred business is approved and completes qualifying spend of $15,000 within 135 days from account opening, you earn a bonus of $300.

## Annual Limits
- You can earn up to 11 referral bonuses per calendar year.

## Qualification Tips
- Encourage the referred business to use the card for eligible purchases promptly after activation to meet $15,000 within the allowed period.
- Ensure the referral is submitted before the application so it is properly attributed.

## Payout and Compliance
- Bonuses are credited to your account after verification that approval and qualifying spend requirements have been met.
- Referrals should comply with applicable marketing and solicitation rules; only share referral information with contacts who have consented to receive it.

10. Lime Green Account: Your Dedicated Account Manager
   ID: doc_business_checking_accounts_lime_green_003
   Score: 13.3345
   Content: ## Response commitments
- Direct messages receive a response within 2 business hours.
- When calling the priority line, the maximum expected wait is 6 minutes.

## How to reach your manager
- Send a secure message from within your account's support center and select the option to route to your dedicated manager.
- For urgent matters, call the priority support line; your call is queued with elevated priority and subject to the 6 minute maximum wait.

## Getting the most out of manager support
- Provide context upfront:
  - The specific transaction or transfer you need help with.
  - Any relevant dates and counterparties.
  - Screenshots of error messages (if applicable).
- Set your preferred contact method so your manager can follow up quickly.
- For time-sensitive requests, note the deadline in your initial message; your manager will respond within 2 business hours.

## Escalations
- If an issue requires faster handling than messaging, use the priority phone line for a live update within the 6 minute window.

## Referral program for Lime Green members

As a Rho-Bank checking account holder, you can refer other businesses to Lime Green and earn substantial rewards:

- **Your bonus**: $200 for each successful referral
- **Their bonus**: $150 welcome bonus for the referred business
- **Annual cap**: 12 referrals per year
- **Qualification**: Referred business must deposit $15,000 within 90 days
- **Eligibility**: You must have maintained checking account status with Rho-Bank for a minimum of 90 days.

Speak with your dedicated account manager for personalized referral strategies and tracking.


[Timing: retrieval=1ms, reranking=0ms, total=1ms]

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "id": "skill-1",
  "role": "tool",
  "requestor": "assistant",
  "error": false,
  "turn_idx": 3,
  "timestamp": "2026-11-15T01:52:21.143608"
}
```


</details>

<a id="m004"></a>

### M004 · assistant

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "skill-2",
      "name": "KB_search",
      "arguments": {
        "query": "referral program bonus refer a friend"
      },
      "requestor": "assistant"
    }
  ],
  "is_audio": false,
  "turn_idx": 4,
  "timestamp": "2026-11-15T01:52:21.180312",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 0.03573298100673128,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m005"></a>

### M005 · tool

1. Gold Years Account Referral Program
   ID: doc_checking_accounts_gold_years_account_010
   Score: 23.8749
   Content: ## Refer a friend to Gold Years

Share the benefits of the Gold Years Account with friends and family members who are 62 or older.

### Rewards
- **You receive**: $50 for each successful referral
- **They receive**: $75 as a welcome bonus
- **Annual maximum**: 6 referral bonuses per calendar year

### How to qualify
- The referrer must have maintained checking account status with Rho-Bank for 30 days.
- The person you refer must be eligible for a Gold Years Account (age 62+)
- They must deposit $1,000 within 90 days of account opening

### Referral summary
| Program element | Detail |
|---|---|
| Your bonus | $50 |
| Their bonus | $75 |
| Max referrals/year | 6 |
| Qualifying deposit | $1,000 |
| Deposit deadline | 90 days |
| Customer tenure | 30 days |

### Getting started
1. Find your personalized referral link in your account settings
2. Share it with eligible friends and family
3. Track successful referrals in your rewards dashboard

2. Refer a Friend to Rho-Bank and Earn Rewards
   ID: doc_credit_cards_credit_cards_(general)_020
   Score: 22.1731
   Content: Do you love your Rho-Bank credit card? Share the love with friends and family, and you could both earn rewards! Our referral program makes it easy to invite the people you care about to join Rho-Bank, and when they're approved for a new card and meet the program requirements, you'll both be rewarded.

## How It Works

Participating in our referral program is simple. When you refer someone to apply for a Rho-Bank credit card and they're approved, you may be eligible to receive a referral bonus. The specific bonus amount and requirements vary depending on which credit card you're referring them to—some cards offer cash back bonuses, while others may offer bonus points or statement credits.

## Getting Your Referral Link

To refer a friend, you'll need to generate a unique referral link that's tied to your account. You can do this through the Rho-Bank mobile app, online banking portal, or by contacting our customer service team. Once you have your link, simply share it with friends and family via email, text, or social media. When they use your link to apply and are approved, the referral will be tracked to your account.

## Important Things to Know

To ensure the referral program remains fair for all participants, there are a few guidelines to keep in mind:

- **Weekly Limit**: You can earn referral bonuses for up to 2 successful referrals per week. This is calculated on a rolling 7-day basis, so if you've already had 2 referrals complete in the past week, any additional referrals during that time won't qualify for a bonus.
- **Eligibility**: Not all credit cards participate in the referral program. Before sharing your link, make sure the card you're referring has an active referral offer.
- **Bonus Requirements**: Each referral program has specific requirements that your friend must meet to trigger the bonus, such as making a certain amount of purchases within a specified timeframe after account opening.

## Check Your Referral Status

You can track the status of your referrals at any time through the Rho-Bank mobile app or by contacting customer service. We'll also send you notifications when your referrals are approved and when you earn your bonus.

If you have any questions about the referral program or want to confirm the current offer for your card, please reach out to our customer service team at 1-800-RHO-BANK. We're always happy to help!

3. Platinum Rewards Card: Referral Program - Earn Rewards for Referring Friends
   ID: doc_credit_cards_platinum_rewards_card_008
   Score: 19.5236
   Content: ## How It Works
- Share your referral through your account to invite friends to apply.
- For each friend who is approved and meets the qualifying spend, you earn a referral bonus of $100.

## Qualifying Spend Requirement
- The referred friend must spend at least $1,500 within 90 days of account opening to qualify you for the bonus.

## Annual Limits
- You can earn up to 7 referral bonuses per calendar year.

## Steps to Refer
1. Open the referrals section in your account.
2. Send your referral using the available sharing options.
3. Track the status of pending referrals in your dashboard.

## Payout Timing and Eligibility
- Bonuses are typically credited after the referred applicant is approved and meets the $1,500 spend requirement within 90 days.
- Self-referrals or duplicate applications do not qualify.

## Tips
- Share with friends who are likely to benefit from the card's features.
- Remind your referral to meet the $1,500 spend threshold within 90 days.
- Ensure your account is in good standing to receive bonuses promptly.

4. Dark Green Account Referral Program
   ID: doc_checking_accounts_dark_green_account_010
   Score: 18.9590
   Content: ## Share the Dark Green experience

Refer others to the Dark Green Account and earn rewards when they join.

### Referral rewards
- **Your bonus**: $40 for each qualifying referral
- **Their bonus**: $30 welcome bonus
- **Maximum per year**: 6 referral bonuses

### Qualification criteria
To qualify for the referral bonus:
1. You must satisfy the 45-day minimum as a Rho-Bank checking customer.
2. The person you refer must open a Dark Green Account
3. They must deposit at least $1,000 within 60 days of opening

### Program details
| Aspect | Value |
|---|---|
| Referrer bonus | $40 |
| Referred bonus | $30 |
| Annual cap | 6 referrals |
| Minimum deposit | $1,000 |
| Deposit window | 60 days |
| Tenure required | 45 days |

### Bonus payment
- Bonuses are credited within 5-7 business days after qualification
- Both you and the new member must maintain your accounts in good standing

5. Business Silver Rewards Card: Referral Program - Earn Rewards for Referring Businesses
   ID: doc_business_credit_cards_business_silver_rewards_card_013
   Score: 18.1711
   Content: ## What you can earn
- Earn $100 for each successful referral that is approved and meets the qualifying spend requirement
- You can earn up to 10 referral bonuses per calendar year

## Qualifying spend requirement
- The referred business must spend at least $3,000 within 90 days of account opening for you to receive the bonus

## How to refer
- Share a referral through the official referral channel so applications are tracked correctly
- Ensure the referred business uses your referral details when applying

## Tracking and payout
- After the referred business is approved and completes the qualifying spend, your $100 bonus will be processed according to program rules
- If a referral does not appear, contact support with the referred business name and application date so it can be investigated

6. Silver Zoom Card: Referral Program - Earn Rewards for Referring Logistics Businesses
   ID: doc_business_credit_cards_silver_zoom_card_011
   Score: 17.7380
   Content: ## How the referral program works
- Earn a referral bonus of $150 for each referred logistics business that is approved and meets the qualifying spend requirement
- Bonuses are capped at 10 per calendar year

## Qualifying activity for your referral
- The referred business must complete purchases totaling $7,500 within 90 days of account opening
- Only one referrer is credited per approved account

## Program timing
- No new referrals are accepted after 2025-10-01

## How to refer
- Share your referral link or submit the referral through your account portal before the referred business applies
- Ensure the referred business uses your link or is otherwise properly attributed during application
- Track referral status within your account until the qualifying spend threshold of $7,500 is met

## Payout details
- Bonuses are typically issued to the referrer after the referred business satisfies the $7,500 requirement within 90 days
- If the referred business returns purchases or does not meet the requirement, no bonus is issued

7. Business Gold Rewards Card: Referral Program - Earn Rewards for Referring Businesses
   ID: doc_business_credit_cards_business_gold_rewards_card_010
   Score: 17.5119
   Content: ## How the Referral Bonus Works
- Earn $200 for each successful referral who is approved and meets the qualifying spend.
- You can earn up to 8 referral bonuses per calendar year.

## Qualifying Spend Requirement
- The referred business must spend $7,500 within 90 from account opening to qualify your bonus.

## Program Timeline
- The referral program accepts new referrals until 2025-09-15. Referrals submitted after this date are not eligible.

## How to Refer
- Generate your unique referral link from your account’s referral center.
- Share the link directly with businesses that consent to receive it.
- Track application status and eligibility in the referral dashboard.

## Payouts
- Once the referred account is approved and completes $7,500 within 90, your $200 is queued for issuance to your account.

## Rules and Best Practices
- Self-referrals are not permitted.
- Share referral invitations only with contacts who have given permission to receive them.
- If a referral applies without your link, the referral may not be attributed.
- Program terms, eligible industries, and promotional availability may change without notice prior to 2025-09-15.

8. Beige Account Referral Program
   ID: doc_business_checking_accounts_beige_012
   Score: 16.9586
   Content: ## Enterprise referral program

Refer other enterprise-level businesses to the Beige Account and earn premium referral rewards.

### Premium rewards
- **Your reward**: $500 for each qualifying referral
- **Their reward**: $350 welcome bonus
- **Annual maximum**: 15 referral bonuses per calendar year

### Qualification criteria
To earn a referral bonus:
1. Referrer tenure requirement: 120 days since opening your first checking account with us.
2. The referred enterprise must open a Beige Account
3. They must deposit at least $100,000 within 120 days

### Referral details
| Detail | Amount |
|---|---|
| Referrer bonus | $500 |
| Referred bonus | $350 |
| Maximum per year | 15 |
| Required deposit | $100,000 |
| Deposit window | 120 days |
| Minimum tenure | 120 days |

### How to participate
1. Contact your dedicated relationship manager for referral materials
2. Introduce qualified enterprises to the Beige Account benefits
3. Your relationship manager can facilitate introductions and track referrals
4. Bonuses are credited after all qualification requirements are confirmed

### Enterprise considerations
- Referrals must be for new Beige Account relationships
- Both enterprises must maintain accounts in good standing
- Premium referral bonuses reflect the enterprise-level relationship value

9. FAQ: Checking Account Referrals
   ID: doc_bank_accounts_bank_accounts_(general)_048
   Score: 15.1066
   Content: ## Frequently asked questions about checking account referrals

### How many people can I refer at once?
You can have multiple referrals in progress, but you can only receive a maximum of 2 referral bonuses in any rolling 9-day window. If you exceed this limit, additional referrals will be automatically denied until enough time passes.

### Can I refer someone who used to have a Rho-Bank account?
No. The referred person must be a new Rho-Bank customer with no existing or closed accounts within the past 12 months. Former customers must wait 12 months after their last account closure before being eligible as a referral.

### Can I refer someone who lives at the same address as me?
No. The referrer and referred person cannot be registered at the same address. This restriction helps prevent abuse of the referral program.

### What counts as a qualifying deposit?
The qualifying deposit must be new money brought into Rho-Bank. Transfers from another Rho-Bank account do not count. The deposit can come from an external bank transfer, direct deposit, mobile check deposit, or cash/check deposit at a branch.

### What happens if the person I referred closes their account early?
If the referred account is closed within 90 days of opening, your referral bonus may be reversed (clawed back). Both accounts must remain in good standing for bonuses to be retained.

### Can I combine the referral bonus with other promotions?
No. The referral bonus cannot be combined with other new account promotions or sign-up bonuses. Only one promotional offer can be applied per new account.

### What do the referral statuses mean?
- **COMPLETE**: The referral was successful and bonuses will be paid.
- **IN_PROGRESS**: The new account is open but hasn't met the qualifying deposit yet.
- **NO_PROGRESS**: The referred person hasn't started an application.
- **APPLIED**: An application has been submitted and is being reviewed.
- **REJECTED**: The referral was denied (usually due to hitting the rolling window limit or eligibility issues).
- **ERROR**: A system error occurred; try again later or contact support.

### Why was my referral rejected?
Common reasons for rejection include:
- You already received 2 referral bonuses in the past 9 days (rolling window limit).
- The referred person already has or recently had a Rho-Bank account.
- You and the referred person are registered at the same address.
- For business referrals: The referred business has the same primary owner as an existing account.

### How long do I have to wait after a rejection to refer again?
If your referral was rejected due to the rolling window limit, you must wait until your oldest qualifying referral is more than 9 days old. The limit is based on a rolling window, so you become eligible again as older referrals age out.

### Can I refer someone for a business checking account?
Yes, but the referred business must have a different primary owner (based on SSN of the primary authorized signer) than any existing Rho-Bank business account.

### Do I need to have the same account type to refer someone for it?
No. Referrer eligibility hinges on how long you've been a Rho-Bank checking customer, not which product you currently use. The tenure threshold is measured from when you opened your very first checking account with us. Someone with a Navy Blue account can refer others for World Blue, True Blue, or any other checking product—provided they've met the duration requirement.

### How long does the referred person have to make the qualifying deposit?
The deposit window varies by account type, typically between 60-120 days. Check the specific account's referral terms for the exact timeframe. After the deposit is made, it must remain in the account for at least 30 additional days.

10. Silver Rewards Card: Referral Program - Earn Rewards for Referring Friends
   ID: doc_credit_cards_silver_rewards_card_011
   Score: 14.9917
   Content: ## What You Earn
- Receive 75 for each successful referral
- You can earn up to 7 referral bonuses per calendar year

## What Your Referral Must Do
- The referred person must be approved and spend at least $750 within 60 days of account opening

## How to Refer
1. Share your referral link or code with friends and colleagues
2. Ensure they apply using your link or code so the referral is tracked
3. You’ll be notified when the referral meets the qualifying spend requirement

## Payout Timing
- Your bonus typically posts within one to two billing cycles after the referred account meets the $750 requirement

## Program Tips
- Remind your referral to activate their card promptly and add recurring bills to help them meet $750 within 60 days
- Track your annual count to stay within the 7 limit


[Timing: retrieval=1ms, reranking=0ms, total=1ms]

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "id": "skill-2",
  "role": "tool",
  "requestor": "assistant",
  "error": false,
  "turn_idx": 5,
  "timestamp": "2026-11-15T01:52:21.182700"
}
```


</details>

<a id="m006"></a>

### M006 · assistant

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "skill-3",
      "name": "KB_search",
      "arguments": {
        "query": "business checking account types overview deposit requirements"
      },
      "requestor": "assistant"
    }
  ],
  "is_audio": false,
  "turn_idx": 6,
  "timestamp": "2026-11-15T01:52:30.008661",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 8.824818000997766,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m007"></a>

### M007 · tool

1. Internal: Retrieving Customer Account Information
   ID: doc_bank_accounts_bank_accounts_(general)_009
   Score: 14.1359
   Content: ## Overview

Use get_all_user_accounts_by_user_id_3847 to retrieve the bank accounts (checkings, savings) for a customer.

## When to Use

This tool is essential for:
1. Checking eligibility requirements for opening new accounts (existing account status, balances, account tenure, number of accounts)
2. Verifying pre-closure requirements when closing accounts
3. Looking up account details for customer service inquiries

## Parameters

The tool requires the customer's user_id and returns all account information including:
- account_id
- account_type
- account_class
- status
- balance
- date_opened

2. Bronze Saver Account specifications and requirements
   ID: doc_business_savings_accounts_bronze_saver_account_002
   Score: 14.1137
   Content: ## Specifications
| Item | Details |
| --- | --- |
| Minimum opening deposit | $0 |
| Interest compounding frequency | daily |
| Linked Rho-Bank business checking required | Yes |

## Requirements guidance
- Ensure a linked Rho-Bank business checking account remains active if Yes is required for your setup.
- Confirm your compounding preference is set to daily in your account details.
- Verify the initial funding meets or exceeds $0.

3. Internal: Opening Business Savings Accounts
   ID: doc_bank_accounts_bank_accounts_(general)_004
   Score: 13.5473
   Content: ## Description

Procedure for opening business savings accounts. Eligibility requirements: 1) Customer must be verified, 2) Customer must already have at least one business checking account with status OPEN, 3) Customer cannot have more than 4 business savings accounts, 4) Customer must not have any accounts with negative balances, 5) Existing business checking account must have been open for at least 30 days, 6) Existing business checking account must have a balance of at least $2,500. Steps: 1) Verify customer identity, 2) Check eligibility requirements, 3) Confirm account selection with customer (business savings account_class options include Bronze Saver Account, Silver Saver Account, etc.), 4) Use open_bank_account_4821 to open the account, 5) Ask the customer if they would like you to transfer the opening deposit from their business checking account now. If yes, use transfer_funds_between_bank_accounts_7291 to transfer the required amount. If no, inform them they have 30 days to fund the account (via internal transfer or external deposit) or the account will be closed.

## Eligibility Requirements

Confirm all of the following before proceeding:
- Customer identity is verified.
- Customer has at least one business checking account with status OPEN.
- Customer has fewer than 4 existing business savings accounts.
- Customer has no accounts with negative balances.
- At least one existing business checking account has been open for at least 30 days.
- That business checking account has a current balance of at least $2,500.

Notes:
- Use the qualifying OPEN business checking account that meets both the tenure and balance thresholds as the source for the optional opening deposit transfer.

## Step-by-Step Procedure

1) Verify customer identity.
2) Check eligibility requirements (see list above).
3) Confirm account selection with the customer:
   - Ask for the desired business savings account_class (e.g., Bronze Saver Account, Silver Saver Account, etc.).
   - Ensure you capture the exact official account_class name ending with “Account.”
4) Open the new business savings account using the agent tool (see Tool Instructions below).
5) Funding the opening deposit:
   - Ask the customer if they want you to transfer the opening deposit now from their eligible business checking account.
   - If yes: initiate the internal transfer using the agent tool (see Tool Instructions below).
   - If no: inform the customer they have 30 days to fund the account via internal transfer or external deposit; otherwise, the account will be closed.

## Agent Tool Instructions

The AGENT calls these tools directly to perform actions on behalf of the customer. Do not expose tool details to the customer.

### Tool: open_bank_account_4821

- Signature:
  - open_bank_account_4821(user_id, account_type, account_class)
- When to call:
  - After eligibility is confirmed and the customer has selected the desired business savings account_class.
- How to call:
  - Set account_type to 'savings'.
  - Set account_class to the exact official name provided by the customer (e.g., 'Bronze Saver Account').
- Expected outcome:
  - Returns a new savings account record (capture the new account_id for subsequent actions).

### Tool: transfer_funds_between_bank_accounts_7291

- Signature:
  - transfer_funds_between_bank_accounts_7291(source_account_id, destination_account_id, amount)
- When to call:
  - Only if the customer authorizes transferring the opening deposit now.
- How to call:
  - source_account_id: the qualifying OPEN business checking account that meets the 30-day tenure and $2,500 balance requirements.
  - destination_account_id: the newly opened business savings account_id.
  - amount: the required opening deposit amount confirmed with the customer.
- If the transfer fails (e.g., insufficient funds):
  - Inform the customer and remind them they have 30 days to fund the account via internal transfer or external deposit, or the account will be closed.

## Checklist Before Opening

- Customer identity verified.
- OPEN business checking account identified and qualified (≥ 30 days open and ≥ $2,500 balance).
- Savings account count confirmed is < 4.
- No negative balances across any accounts.
- Customer-confirmed account_class captured exactly.

## Post-Opening Actions

- If the customer funds now: complete the transfer and confirm success.
- If the customer defers funding: clearly communicate the 30-day deadline and acceptable methods (internal transfer or external deposit), and note that the account will be closed if not funded within that timeframe.

4. Internal: Opening Business Checking Accounts
   ID: doc_bank_accounts_bank_accounts_(general)_003
   Score: 13.1054
   Content: ## Eligibility Requirements

To open a business checking account, ensure all of the following are true:
1. The customer is verified.
2. The customer has at least one existing personal checking account with status OPEN.
3. The customer does not exceed 6 business checking accounts.
4. The customer has no accounts with status CLOSED.
5. The customer's existing checking account has a balance of at least $500.

## Opening Procedure

1. Verify customer identity.
2. Check eligibility requirements listed above.
3. Confirm the customer's desired account_class selection.
   - Business checking account_class options include Navy Blue, Cobalt Blue, True Blue, etc.
4. Use open_bank_account_4821 to open the account.

5. Internal: Applying Credits and Rebates to Checking Accounts
   ID: doc_bank_accounts_bank_accounts_(general)_017
   Score: 12.8593
   Content: ## Overview

This document describes the policy and procedure for agents to apply credits to customer checking accounts. Credits may only be applied to checking accounts (not savings accounts or other account types). The apply_checking_account_credit_5829 tool is used to add a credit transaction to a checking account.

## Eligible Circumstances for Applying Credits

Agents are authorized to apply credits to checking accounts ONLY in the following circumstances:

### 1. Missing Rebates

If a rebate that should have been applied to the customer's account has not yet been applied, and the customer meets all eligibility requirements for that rebate, the agent may apply the credit. Before applying:
- Verify the customer is eligible for the rebate based on documented rebate policies
- Confirm the rebate has not already been applied by checking the account's transaction history
- Ensure the rebate amount matches what is specified in the applicable rebate policy

### 2. Fee mischarges

If any fees on the customer's account do not match the correct amounts per the documented fee schedule, the agent must identify all fee discrepancies and apply a credit for the net correction. Before applying:
- Review the account terms and documented fee structures to identify all fees that differ from what should have been charged
- Check the transaction history to confirm each fee discrepancy
- Ensure the credit amount reflects the net correction across all identified fee discrepancies

## Credit Types

When applying a credit, use the appropriate credit_type:
- `rebate_credit`: For rebates that should have been applied but were missing
- `fee_refund`: For refunding fees that were incorrectly charged

## Procedure

1. Verify the customer's identity and account ownership
2. Confirm the account is a checking account (credits cannot be applied to savings or other account types)
3. Verify the customer meets one of the eligible circumstances listed above
4. Calculate the correct credit amount based on the rebate policy or fee that was overcharged
5. Use the apply_checking_account_credit_5829 tool to apply the credit
6. Inform the customer of the applied credit and new account balance

## Agent Tool Usage (Internal Only)

- Tool: apply_checking_account_credit_5829(account_id, amount, credit_type)
  - When to call: After confirming the customer meets one of the eligible circumstances above
  - How to set parameters:
    - account_id: The checking account ID to credit
    - amount: The positive dollar amount to credit (must be greater than 0)
    - credit_type: Must be one of 'rebate_credit' or 'fee_refund'
  - Expected outcome: Adds a credit transaction to the checking account and updates the account balance

The apply_checking_account_credit_5829 tool may only be called ONCE per checking account per customer interaction. After a credit is applied to a checking account, the system enforces a 14-day cooldown period before another credit can be applied to that same account. Because only one credit call is allowed per account, if multiple corrections are needed for the same account (e.g., both fee refunds and missing rebates), combine them into a single credit with the total amount and use the credit_type that applies to the majority of the corrections.

## Important Restrictions

- Credits may ONLY be applied to checking accounts. Savings accounts and other account types are not eligible.
- Credits may only be applied for the two circumstances listed above. Do not apply credits for any other reason without supervisor approval.
- Always document the reason for the credit by selecting the appropriate credit_type. 
- The credit amount must match the exact rebate or fee amount - do not round or estimate.

6. Gold Saver Account: How Automated Sweeps Work with Business Checking
   ID: doc_business_savings_accounts_gold_saver_account_002
   Score: 11.7354
   Content: ## Overview of automated sweeps
Automated sweeps move available funds between your business checking and savings to help you maintain working capital while capturing interest on excess balances.

### When sweeps run
- Sweeps are evaluated on a daily cadence.

### Checking balance threshold
- Your checking account aims to maintain at least $1,000.
- When available funds exceed this threshold, the excess becomes eligible to move into savings.

### What happens during a sweep
- The system checks your checking balance against the threshold.
- Eligible excess is transferred into savings to optimize idle funds.
- If your checking balance is at or below $1,000, no sweep to savings occurs.

### Managing sweeps
- You can monitor sweep activity in your account activity view.
- If you anticipate large outgoing payments, ensure your checking balance remains at or above $1,000 so that a sweep does not reduce funds needed for those payments.

7. Internal: Closing Business Savings Accounts
   ID: doc_bank_accounts_bank_accounts_(general)_008
   Score: 11.2339
   Content: ## Pre-Closure Requirements

Verify all of the following before closing:
- If an early closure fee applies, the account balance must be at least the fee amount; otherwise, account balance (current_holdings) must be $0. The fee is deducted directly from the account balance and there is no alternative payment method.
- Account status is OPEN
- No pending transactions for this account
- Customer must have at least one active business checking account remaining (business savings requires a linked business checking account)

## Tier-Specific Closure Requirements

- ENTRY TIER (Bronze Saver Account)
  - Early closure fee: $75 if closed within 90 days
  - Notice period: 10 days

- MID TIER (Silver Saver Account)
  - Early closure fee: $125 if closed within 120 days
  - Notice period: 14 days

- PREMIUM TIER (Gold Saver Account)
  - Early closure fee: $250 if closed within 180 days
  - Notice period: 21 days
  - Requires supervisor review

- ELITE TIER (Platinum Reserve Account)
  - Early closure fee: $500 if closed within 270 days
  - Notice period: 30 days
  - Requires manager approval

## Closure Procedure

1. Verify pre-closure requirements are met.
2. Determine the account tier and applicable fees/notice period.
3. For PREMIUM tier, obtain supervisor review. For ELITE tier, obtain manager approval.
4. Use close_bank_account_7392 to close the account.

8. Internal: Checking Account Referral Program Terms and Restrictions
   ID: doc_bank_accounts_bank_accounts_(general)_047
   Score: 10.6325
   Content: ## Program overview
Each checking account type has its own referral bonus amounts and qualification requirements. This document covers the general terms and restrictions that apply to all checking account referral programs. Before giving any recommendations or information on referral terms, you must check that the user is eligible to submit referrals first, as users who are not eligible to submit referrals while being given recommendations by the agent tend to leave dissatisfactory reviews. 

## Rolling window limit
- You can receive at most 2 referral bonuses in any rolling 9-day window.
- If you attempt to receive more than 2 referrals in a single 9-day period, the third referral (and any subsequent referrals in that window) will be automatically denied.
- This limit applies across all checking account types; referrals from different accounts count toward the same 9-day cap.
- A rolling 9-day window means the count is evaluated based on the exact timestamps of your most recent referral bonuses, not calendar weeks.
- Auto-denied referrals due to the limit cannot be reinstated within the same 9-day window.

## Eligibility restrictions
- The referred person must be a new Rho-Bank customer with no existing checking, savings, or closed accounts within the past 12 months.
- The referrer and referred person cannot be registered at the same address.
- The referred person must be 18 years or older, except for the Light Green Account which allows minors with a guardian.
- For business accounts: The referred business must have a different primary owner than any existing Rho-Bank business account, based on the SSN of the primary authorized signer.

## Referrer tenure policy
- Every referral program requires the referrer to meet a tenure threshold before participating.
- This threshold is calculated from when you first became a Rho-Bank checking customer—specifically, the date your earliest checking account was opened.
- The type of account you currently hold is irrelevant to this calculation. Whether you have a basic or premium product, the tenure measurement remains the same.
- Consequently, holding one account type does not prevent you from referring someone to a different account type, as long as the duration since your first account meets or exceeds the program's stated minimum.

## Bonus conditions
- The qualifying deposit must be new money and cannot be transferred from another Rho-Bank account.
- The qualifying deposit must remain in the account for at least 30 days after the qualifying period ends.
- If the referred account is closed within 90 days of opening, the referral bonus may be reversed (clawback provision).

## Stacking restrictions
- The referral bonus cannot be combined with other new account promotions or sign-up bonuses.
- Only one referral code can be applied per new account.

## Referral status definitions
- COMPLETE — The referred person has successfully opened a new account and met the criteria to receive the referral bonus.
- IN_PROGRESS — The referred person has successfully opened a new account and is working toward meeting the qualifying deposit requirement.
- NO_PROGRESS — The referred person has not applied yet; no progress has been made.
- APPLIED — The referred person has submitted an application and is awaiting a decision.
- REJECTED — The referral has been denied (e.g., rolling window limit exceeded, ineligible referral).
- ERROR — A system error occurred during the referral process.

## Practical guidance
- Track the timing of your last two successful referral bonuses before sending additional referrals.
- If a referral is denied for hitting the rolling window limit, wait until enough time has passed to drop under the cap before attempting another.
- Both accounts must remain in good standing for bonuses to be paid.

9. Linked Checking Account APY Boost: Selection Policy
   ID: doc_bank_accounts_bank_accounts_(general)_046
   Score: 10.6193
   Content: ## Multiple Checking Account APY Boost Selection Policy

When a customer holds multiple Rho-Bank checking accounts that each provide an APY boost on their savings account, the boosts do NOT stack. Only the highest applicable checking account APY boost is applied to the customer's savings account.

### How it works

1. The system identifies all active Rho-Bank checking accounts linked to the customer's profile.
2. For each checking account, the corresponding APY boost for the savings account type is determined.
3. Only the HIGHEST checking account APY boost is applied to the savings account.
4. Other checking account boosts are not added on top.

### Example

If a customer with a Gold Savings Account holds:
- Green Account (checking): +0.75% APY boost
- Purple Account (checking): +0.1% APY boost

The customer receives only the Green Account boost of +0.75% (the highest), not the sum of both.

### Important distinctions

- Checking account APY boosts do NOT stack with each other.
- However, checking account APY boosts DO stack with other types of bonuses, such as:
  - Credit card APY bonuses (only highest credit card bonus applies)
  - Relationship bonuses for holding multiple Rho-Bank products
  - Account tier bonuses

### Why this policy exists

This policy ensures that customers receive a meaningful benefit for holding premium checking accounts while maintaining sustainable interest rates across the product portfolio.

### Agent Responsibility

When investigating interest discrepancies for customers with multiple checking accounts, agents must:
1. Identify all checking accounts the customer holds
2. Determine which checking account provides the highest APY boost for the savings account type
3. Verify that the system is applying the highest boost, not a lower one
4. If the system selected the wrong checking account, calculate the correct APY and apply an interest correction

10. Green Fee-Free Account Referral Program
   ID: doc_checking_accounts_green_fee-free_account_007
   Score: 10.4480
   Content: ## Refer and earn

Help others discover the Green Fee-Free Account and earn rewards for successful referrals.

### Bonus structure
- Your reward: $20 per successful referral
- New member reward: $35 welcome bonus
- Annual limit: 4 referrals per year

### Qualification requirements
For a referral to count as successful:
- The new account holder must deposit at least $300
- This deposit must be made within 60 days of opening their account
- Your Rho-Bank checking relationship must span at least 30 days.

### Quick reference
| Detail | Amount |
|---|---|
| You earn | $20 |
| They earn | $35 |
| Max per year | 4 |
| Required deposit | $300 |
| Deposit deadline | 60 days |
| Referrer eligibility | 30 days |

### How to participate
1. Access your referral link from your account dashboard
2. Share with potential new members
3. Track your referrals and bonuses in the rewards section


[Timing: retrieval=2ms, reranking=0ms, total=2ms]

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "id": "skill-3",
  "role": "tool",
  "requestor": "assistant",
  "error": false,
  "turn_idx": 7,
  "timestamp": "2026-11-15T01:52:30.012987"
}
```


</details>

<a id="m008"></a>

### M008 · assistant

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "skill-4",
      "name": "KB_search",
      "arguments": {
        "query": "how to submit a referral referral link business checking"
      },
      "requestor": "assistant"
    }
  ],
  "is_audio": false,
  "turn_idx": 8,
  "timestamp": "2026-11-15T01:52:30.027131",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 0.013562533000367694,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m009"></a>

### M009 · tool

1. Silver Zoom Card: Referral Program - Earn Rewards for Referring Logistics Businesses
   ID: doc_business_credit_cards_silver_zoom_card_011
   Score: 24.7962
   Content: ## How the referral program works
- Earn a referral bonus of $150 for each referred logistics business that is approved and meets the qualifying spend requirement
- Bonuses are capped at 10 per calendar year

## Qualifying activity for your referral
- The referred business must complete purchases totaling $7,500 within 90 days of account opening
- Only one referrer is credited per approved account

## Program timing
- No new referrals are accepted after 2025-10-01

## How to refer
- Share your referral link or submit the referral through your account portal before the referred business applies
- Ensure the referred business uses your link or is otherwise properly attributed during application
- Track referral status within your account until the qualifying spend threshold of $7,500 is met

## Payout details
- Bonuses are typically issued to the referrer after the referred business satisfies the $7,500 requirement within 90 days
- If the referred business returns purchases or does not meet the requirement, no bonus is issued

2. Business Bronze Rewards Card: Referral Program - Earn Rewards for Referring Businesses
   ID: doc_business_credit_cards_business_bronze_rewards_card_011
   Score: 23.6597
   Content: ## What You Can Earn
- Receive $75 for each successful referral.
- You can earn up to 7 referral bonuses per calendar year.

## What Makes a Referral Successful
- The referred business must be approved for the card.
- The referred business must complete at least $1,750 in net purchases within 90 days of account opening.

## How to Refer
1. Share your referral link or code with another business.
2. Ensure they apply using your link or enter your code during their application.
3. You will be notified when the referral is approved and has met the $1,750 requirement within 90 days.

## Tracking Your Bonuses
- Monitor referral status, qualifying spend progress, and paid bonuses in your account dashboard.
- If a referred account is closed or reversed, any unpaid referral bonus may be canceled.

## Best Practices
- Encourage referrals to complete their initial purchases early to meet the $1,750 requirement within 90 days.
- Remind referrals to use your link or code so your bonus is tracked correctly.

3. Generating a Credit Card Referral Link (Internal)
   ID: doc_credit_cards_credit_cards_(general)_009
   Score: 22.8184
   Content: ## Pre-check before providing the referral tool
- Search the knowledge base to confirm the specific card has a documented referral program.
- Verify the customer’s understanding of referral terms. If the customer cites terms that do not match any documented program, clarify the discrepancy.
- If no referral program is documented for the requested card, or if the user’s claimed terms are incorrect, or if there is reason to believe the referral will be automatically rejected, explain why and do not provide a referral link tool. Do not transfer to a human in these cases.

## How the user generates their referral link
- Provide the customer with this tool and instruct them to run it themselves:
  - `get_referral_link(user_id: str, card_name: str)`
- Tell the customer to pass their own user_id and the exact card name (for example, 'Gold Rewards Card').
- When the tool is called successfully, a referral record is created with status 'NO_PROGRESS'. The referred person can then use the generated link to apply.

## Important reminders
- Weekly limit: Customers can receive at most 2 referral bonuses in any rolling 7-day window; the third and subsequent referrals in that window are automatically denied.
- Agents must not generate the link on the customer’s behalf.
- Reiterate the correct referral terms as documented to prevent confusion and complaints.

4. Business Gold Rewards Card: Referral Program - Earn Rewards for Referring Businesses
   ID: doc_business_credit_cards_business_gold_rewards_card_010
   Score: 22.6162
   Content: ## How the Referral Bonus Works
- Earn $200 for each successful referral who is approved and meets the qualifying spend.
- You can earn up to 8 referral bonuses per calendar year.

## Qualifying Spend Requirement
- The referred business must spend $7,500 within 90 from account opening to qualify your bonus.

## Program Timeline
- The referral program accepts new referrals until 2025-09-15. Referrals submitted after this date are not eligible.

## How to Refer
- Generate your unique referral link from your account’s referral center.
- Share the link directly with businesses that consent to receive it.
- Track application status and eligibility in the referral dashboard.

## Payouts
- Once the referred account is approved and completes $7,500 within 90, your $200 is queued for issuance to your account.

## Rules and Best Practices
- Self-referrals are not permitted.
- Share referral invitations only with contacts who have given permission to receive them.
- If a referral applies without your link, the referral may not be attributed.
- Program terms, eligible industries, and promotional availability may change without notice prior to 2025-09-15.

5. Internal: Checking Account Referral Program Terms and Restrictions
   ID: doc_bank_accounts_bank_accounts_(general)_047
   Score: 22.5423
   Content: ## Program overview
Each checking account type has its own referral bonus amounts and qualification requirements. This document covers the general terms and restrictions that apply to all checking account referral programs. Before giving any recommendations or information on referral terms, you must check that the user is eligible to submit referrals first, as users who are not eligible to submit referrals while being given recommendations by the agent tend to leave dissatisfactory reviews. 

## Rolling window limit
- You can receive at most 2 referral bonuses in any rolling 9-day window.
- If you attempt to receive more than 2 referrals in a single 9-day period, the third referral (and any subsequent referrals in that window) will be automatically denied.
- This limit applies across all checking account types; referrals from different accounts count toward the same 9-day cap.
- A rolling 9-day window means the count is evaluated based on the exact timestamps of your most recent referral bonuses, not calendar weeks.
- Auto-denied referrals due to the limit cannot be reinstated within the same 9-day window.

## Eligibility restrictions
- The referred person must be a new Rho-Bank customer with no existing checking, savings, or closed accounts within the past 12 months.
- The referrer and referred person cannot be registered at the same address.
- The referred person must be 18 years or older, except for the Light Green Account which allows minors with a guardian.
- For business accounts: The referred business must have a different primary owner than any existing Rho-Bank business account, based on the SSN of the primary authorized signer.

## Referrer tenure policy
- Every referral program requires the referrer to meet a tenure threshold before participating.
- This threshold is calculated from when you first became a Rho-Bank checking customer—specifically, the date your earliest checking account was opened.
- The type of account you currently hold is irrelevant to this calculation. Whether you have a basic or premium product, the tenure measurement remains the same.
- Consequently, holding one account type does not prevent you from referring someone to a different account type, as long as the duration since your first account meets or exceeds the program's stated minimum.

## Bonus conditions
- The qualifying deposit must be new money and cannot be transferred from another Rho-Bank account.
- The qualifying deposit must remain in the account for at least 30 days after the qualifying period ends.
- If the referred account is closed within 90 days of opening, the referral bonus may be reversed (clawback provision).

## Stacking restrictions
- The referral bonus cannot be combined with other new account promotions or sign-up bonuses.
- Only one referral code can be applied per new account.

## Referral status definitions
- COMPLETE — The referred person has successfully opened a new account and met the criteria to receive the referral bonus.
- IN_PROGRESS — The referred person has successfully opened a new account and is working toward meeting the qualifying deposit requirement.
- NO_PROGRESS — The referred person has not applied yet; no progress has been made.
- APPLIED — The referred person has submitted an application and is awaiting a decision.
- REJECTED — The referral has been denied (e.g., rolling window limit exceeded, ineligible referral).
- ERROR — A system error occurred during the referral process.

## Practical guidance
- Track the timing of your last two successful referral bonuses before sending additional referrals.
- If a referral is denied for hitting the rolling window limit, wait until enough time has passed to drop under the cap before attempting another.
- Both accounts must remain in good standing for bonuses to be paid.

6. Light Blue Account Referral Program
   ID: doc_checking_accounts_light_blue_account_007
   Score: 22.2020
   Content: ## Earn rewards by referring friends

Share the Light Blue Account with others and earn cash bonuses.

### What you earn
- Referral bonus: $30 for each successful referral
- Maximum referrals: 5 per calendar year

### What they receive
- Welcome bonus: $20 when they open and fund their account

### Requirements

| Requirement | Detail |
|---|---|
| Qualifying deposit | $500 |
| Deposit window | Within 60 days of account opening |
| Referrer tenure | 30 days |

### How it works
1. Share your unique referral link with friends and family
2. They open a Light Blue Account using your link
3. They deposit at least $500 within 60 days
4. You receive $30 and they receive $20

### Eligibility
- To qualify as a referrer, you must have been a Rho-Bank checking account holder for 30 days or longer.
- You can earn up to 5 referral bonuses per calendar year

7. Green Rewards Card: Referral Program - Earn Rewards for Referring Businesses
   ID: doc_business_credit_cards_green_rewards_card_010
   Score: 21.8171
   Content: ## How the Referral Program Works
- Share your referral link with a business contact.
- When a referred business is approved and meets the qualifying spend, you earn 75.

## Earning Limits and Timing
- You can earn up to 7 referral bonuses per calendar year.
- The referred business must spend at least $2,250 within 90 days from account opening to qualify your bonus.
- Bonuses are credited after verification that the qualifying criteria have been met.

## Qualifying Criteria
- The referred business must apply through your unique referral link.
- The application must be approved and the account must remain in good standing through the verification date.
- Qualifying purchases exclude cash equivalents, certain fees, and returned transactions.

## Tracking Your Referrals
- View referral status in your rewards section, including approval state and qualifying spend progress.
- You will be notified when a referral meets $2,250 within 90 days and your 75 is pending.

## Tips for Successful Referrals
- Share how the card’s sustainability features align with common business goals.
- Encourage referrals to complete required steps promptly so their spend can count toward the qualification window.

8. Refer a Friend to Rho-Bank and Earn Rewards
   ID: doc_credit_cards_credit_cards_(general)_020
   Score: 21.3940
   Content: Do you love your Rho-Bank credit card? Share the love with friends and family, and you could both earn rewards! Our referral program makes it easy to invite the people you care about to join Rho-Bank, and when they're approved for a new card and meet the program requirements, you'll both be rewarded.

## How It Works

Participating in our referral program is simple. When you refer someone to apply for a Rho-Bank credit card and they're approved, you may be eligible to receive a referral bonus. The specific bonus amount and requirements vary depending on which credit card you're referring them to—some cards offer cash back bonuses, while others may offer bonus points or statement credits.

## Getting Your Referral Link

To refer a friend, you'll need to generate a unique referral link that's tied to your account. You can do this through the Rho-Bank mobile app, online banking portal, or by contacting our customer service team. Once you have your link, simply share it with friends and family via email, text, or social media. When they use your link to apply and are approved, the referral will be tracked to your account.

## Important Things to Know

To ensure the referral program remains fair for all participants, there are a few guidelines to keep in mind:

- **Weekly Limit**: You can earn referral bonuses for up to 2 successful referrals per week. This is calculated on a rolling 7-day basis, so if you've already had 2 referrals complete in the past week, any additional referrals during that time won't qualify for a bonus.
- **Eligibility**: Not all credit cards participate in the referral program. Before sharing your link, make sure the card you're referring has an active referral offer.
- **Bonus Requirements**: Each referral program has specific requirements that your friend must meet to trigger the bonus, such as making a certain amount of purchases within a specified timeframe after account opening.

## Check Your Referral Status

You can track the status of your referrals at any time through the Rho-Bank mobile app or by contacting customer service. We'll also send you notifications when your referrals are approved and when you earn your bonus.

If you have any questions about the referral program or want to confirm the current offer for your card, please reach out to our customer service team at 1-800-RHO-BANK. We're always happy to help!

9. FAQ: Checking Account Referrals
   ID: doc_bank_accounts_bank_accounts_(general)_048
   Score: 20.7171
   Content: ## Frequently asked questions about checking account referrals

### How many people can I refer at once?
You can have multiple referrals in progress, but you can only receive a maximum of 2 referral bonuses in any rolling 9-day window. If you exceed this limit, additional referrals will be automatically denied until enough time passes.

### Can I refer someone who used to have a Rho-Bank account?
No. The referred person must be a new Rho-Bank customer with no existing or closed accounts within the past 12 months. Former customers must wait 12 months after their last account closure before being eligible as a referral.

### Can I refer someone who lives at the same address as me?
No. The referrer and referred person cannot be registered at the same address. This restriction helps prevent abuse of the referral program.

### What counts as a qualifying deposit?
The qualifying deposit must be new money brought into Rho-Bank. Transfers from another Rho-Bank account do not count. The deposit can come from an external bank transfer, direct deposit, mobile check deposit, or cash/check deposit at a branch.

### What happens if the person I referred closes their account early?
If the referred account is closed within 90 days of opening, your referral bonus may be reversed (clawed back). Both accounts must remain in good standing for bonuses to be retained.

### Can I combine the referral bonus with other promotions?
No. The referral bonus cannot be combined with other new account promotions or sign-up bonuses. Only one promotional offer can be applied per new account.

### What do the referral statuses mean?
- **COMPLETE**: The referral was successful and bonuses will be paid.
- **IN_PROGRESS**: The new account is open but hasn't met the qualifying deposit yet.
- **NO_PROGRESS**: The referred person hasn't started an application.
- **APPLIED**: An application has been submitted and is being reviewed.
- **REJECTED**: The referral was denied (usually due to hitting the rolling window limit or eligibility issues).
- **ERROR**: A system error occurred; try again later or contact support.

### Why was my referral rejected?
Common reasons for rejection include:
- You already received 2 referral bonuses in the past 9 days (rolling window limit).
- The referred person already has or recently had a Rho-Bank account.
- You and the referred person are registered at the same address.
- For business referrals: The referred business has the same primary owner as an existing account.

### How long do I have to wait after a rejection to refer again?
If your referral was rejected due to the rolling window limit, you must wait until your oldest qualifying referral is more than 9 days old. The limit is based on a rolling window, so you become eligible again as older referrals age out.

### Can I refer someone for a business checking account?
Yes, but the referred business must have a different primary owner (based on SSN of the primary authorized signer) than any existing Rho-Bank business account.

### Do I need to have the same account type to refer someone for it?
No. Referrer eligibility hinges on how long you've been a Rho-Bank checking customer, not which product you currently use. The tenure threshold is measured from when you opened your very first checking account with us. Someone with a Navy Blue account can refer others for World Blue, True Blue, or any other checking product—provided they've met the duration requirement.

### How long does the referred person have to make the qualifying deposit?
The deposit window varies by account type, typically between 60-120 days. Check the specific account's referral terms for the exact timeframe. After the deposit is made, it must remain in the account for at least 30 additional days.

10. Gold Years Account Referral Program
   ID: doc_checking_accounts_gold_years_account_010
   Score: 20.3544
   Content: ## Refer a friend to Gold Years

Share the benefits of the Gold Years Account with friends and family members who are 62 or older.

### Rewards
- **You receive**: $50 for each successful referral
- **They receive**: $75 as a welcome bonus
- **Annual maximum**: 6 referral bonuses per calendar year

### How to qualify
- The referrer must have maintained checking account status with Rho-Bank for 30 days.
- The person you refer must be eligible for a Gold Years Account (age 62+)
- They must deposit $1,000 within 90 days of account opening

### Referral summary
| Program element | Detail |
|---|---|
| Your bonus | $50 |
| Their bonus | $75 |
| Max referrals/year | 6 |
| Qualifying deposit | $1,000 |
| Deposit deadline | 90 days |
| Customer tenure | 30 days |

### Getting started
1. Find your personalized referral link in your account settings
2. Share it with eligible friends and family
3. Track successful referrals in your rewards dashboard


[Timing: retrieval=2ms, reranking=0ms, total=2ms]

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "id": "skill-4",
  "role": "tool",
  "requestor": "assistant",
  "error": false,
  "turn_idx": 9,
  "timestamp": "2026-11-15T01:52:30.030371"
}
```


</details>

<a id="m010"></a>

### M010 · assistant

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "skill-5",
      "name": "KB_search",
      "arguments": {
        "query": "Cobalt Blue True Blue business checking referral bonus"
      },
      "requestor": "assistant"
    }
  ],
  "is_audio": false,
  "turn_idx": 10,
  "timestamp": "2026-11-15T01:52:35.230079",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 5.19880143100454,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m011"></a>

### M011 · tool

1. True Blue Account: Fee Waivers and Balance Requirements
   ID: doc_business_checking_accounts_true_blue_002
   Score: 26.8743
   Content: ## Waiving your monthly maintenance fee
- You will be charged $75.00 each month unless you meet the waiver threshold.
- The monthly maintenance fee is waived when your balance is at least $50,000 during the statement period.

## Minimum balance requirement vs. fee waiver threshold
- Minimum balance requirement: $25,000 to maintain the account and access premium features.
- Fee waiver threshold: $50,000 to waive the $75.00 monthly maintenance fee.
- Falling below $25,000 may limit access to premium features until your balance is restored.

## Overdrafts and shortfalls
- If your balance goes negative, a per-occurrence overdraft fee of $25.00 may apply.

## How to avoid fees
- Maintain a balance of at least $50,000 to waive the monthly maintenance fee.
- Set internal processes to monitor balances against both $25,000 and $50,000.
- If a shortfall is anticipated, transfer funds promptly to avoid the $25.00 and preserve eligibility for the fee waiver.

## True Blue Referral Program

Refer other high-volume businesses to True Blue and earn significant rewards:

| Benefit | Amount |
| --- | --- |
| Referrer bonus | $350 per referral |
| New member bonus | $250 |
| Maximum referrals per year | 15 |
| Qualifying deposit | $50,000 |
| Deposit window | 120 days |
| Account age requirement | 90 days |

### Referral requirements
- The referred business must deposit $50,000 within 120 days of opening their True Blue account.
- Eligibility is based on how long you've been a Rho-Bank checking customer. The account age threshold is 90 days, calculated from when you opened your oldest checking account.
- Referral bonuses are paid after qualification is confirmed and are subject to the annual limit of 15.

2. FAQ: Blue Account
   ID: doc_checking_accounts_blue_account_010
   Score: 19.3032
   Content: ## Frequently asked questions

### What does a paper statement cost?
Paper statements are available for $2.50 per month.

### What APY do I earn on my balance?
Your Blue Account earns 0.01% APY on balances.

### Can I set low-balance alerts?
Yes. You can enable alerts at a threshold such as $62 so you are notified when your available balance reaches that level.

### How long do external bank transfers take?
Transfers to another bank typically complete in 2 business days.

### What happens if a deposited check is returned unpaid?
If a deposited check is returned by the issuing bank, a returned deposit fee of $15.00 applies.

### Is there a fee to receive a domestic wire?
Yes. Incoming domestic wires are assessed a fee of $12.50 per wire.

### Does the Blue Account have a referral program?
Yes. When you refer someone to open a Blue Account, you earn $35 for each successful referral. The person you refer receives $30 as a welcome bonus.

### What are the requirements for the referral bonus?
The referred person must deposit at least $500 within 60 days of opening their account. A minimum banking relationship of 30 days is required to participate—this is measured from when you first opened any checking account with us.

### Is there a limit to how many referral bonuses I can earn?
Yes. You can earn up to 5 referral bonuses per calendar year.

3. Light Blue Account Referral Program
   ID: doc_checking_accounts_light_blue_account_007
   Score: 18.4540
   Content: ## Earn rewards by referring friends

Share the Light Blue Account with others and earn cash bonuses.

### What you earn
- Referral bonus: $30 for each successful referral
- Maximum referrals: 5 per calendar year

### What they receive
- Welcome bonus: $20 when they open and fund their account

### Requirements

| Requirement | Detail |
|---|---|
| Qualifying deposit | $500 |
| Deposit window | Within 60 days of account opening |
| Referrer tenure | 30 days |

### How it works
1. Share your unique referral link with friends and family
2. They open a Light Blue Account using your link
3. They deposit at least $500 within 60 days
4. You receive $30 and they receive $20

### Eligibility
- To qualify as a referrer, you must have been a Rho-Bank checking account holder for 30 days or longer.
- You can earn up to 5 referral bonuses per calendar year

4. Internal: Opening Business Checking Accounts
   ID: doc_bank_accounts_bank_accounts_(general)_003
   Score: 17.9218
   Content: ## Eligibility Requirements

To open a business checking account, ensure all of the following are true:
1. The customer is verified.
2. The customer has at least one existing personal checking account with status OPEN.
3. The customer does not exceed 6 business checking accounts.
4. The customer has no accounts with status CLOSED.
5. The customer's existing checking account has a balance of at least $500.

## Opening Procedure

1. Verify customer identity.
2. Check eligibility requirements listed above.
3. Confirm the customer's desired account_class selection.
   - Business checking account_class options include Navy Blue, Cobalt Blue, True Blue, etc.
4. Use open_bank_account_4821 to open the account.

5. FAQ: Checking Account Referrals
   ID: doc_bank_accounts_bank_accounts_(general)_048
   Score: 17.7793
   Content: ## Frequently asked questions about checking account referrals

### How many people can I refer at once?
You can have multiple referrals in progress, but you can only receive a maximum of 2 referral bonuses in any rolling 9-day window. If you exceed this limit, additional referrals will be automatically denied until enough time passes.

### Can I refer someone who used to have a Rho-Bank account?
No. The referred person must be a new Rho-Bank customer with no existing or closed accounts within the past 12 months. Former customers must wait 12 months after their last account closure before being eligible as a referral.

### Can I refer someone who lives at the same address as me?
No. The referrer and referred person cannot be registered at the same address. This restriction helps prevent abuse of the referral program.

### What counts as a qualifying deposit?
The qualifying deposit must be new money brought into Rho-Bank. Transfers from another Rho-Bank account do not count. The deposit can come from an external bank transfer, direct deposit, mobile check deposit, or cash/check deposit at a branch.

### What happens if the person I referred closes their account early?
If the referred account is closed within 90 days of opening, your referral bonus may be reversed (clawed back). Both accounts must remain in good standing for bonuses to be retained.

### Can I combine the referral bonus with other promotions?
No. The referral bonus cannot be combined with other new account promotions or sign-up bonuses. Only one promotional offer can be applied per new account.

### What do the referral statuses mean?
- **COMPLETE**: The referral was successful and bonuses will be paid.
- **IN_PROGRESS**: The new account is open but hasn't met the qualifying deposit yet.
- **NO_PROGRESS**: The referred person hasn't started an application.
- **APPLIED**: An application has been submitted and is being reviewed.
- **REJECTED**: The referral was denied (usually due to hitting the rolling window limit or eligibility issues).
- **ERROR**: A system error occurred; try again later or contact support.

### Why was my referral rejected?
Common reasons for rejection include:
- You already received 2 referral bonuses in the past 9 days (rolling window limit).
- The referred person already has or recently had a Rho-Bank account.
- You and the referred person are registered at the same address.
- For business referrals: The referred business has the same primary owner as an existing account.

### How long do I have to wait after a rejection to refer again?
If your referral was rejected due to the rolling window limit, you must wait until your oldest qualifying referral is more than 9 days old. The limit is based on a rolling window, so you become eligible again as older referrals age out.

### Can I refer someone for a business checking account?
Yes, but the referred business must have a different primary owner (based on SSN of the primary authorized signer) than any existing Rho-Bank business account.

### Do I need to have the same account type to refer someone for it?
No. Referrer eligibility hinges on how long you've been a Rho-Bank checking customer, not which product you currently use. The tenure threshold is measured from when you opened your very first checking account with us. Someone with a Navy Blue account can refer others for World Blue, True Blue, or any other checking product—provided they've met the duration requirement.

### How long does the referred person have to make the qualifying deposit?
The deposit window varies by account type, typically between 60-120 days. Check the specific account's referral terms for the exact timeframe. After the deposit is made, it must remain in the account for at least 30 additional days.

6. Navy Blue Business Checking: Complete Guide
   ID: doc_business_checking_accounts_navy_blue_001
   Score: 16.9543
   Content: ## Key Account Costs and Limits

- Monthly maintenance fee: $0.00
- Annual Percentage Yield (APY) on balances: 0.5%
- Daily digital transfer limit: $25,000

### What you can expect day to day
- No minimum balance requirement, so you can use the account flexibly.
- Unlimited digital transfers within the daily limit of $25,000.
- Optional overdraft settings are available if you want coverage on eligible transactions.
- E-statements are included at no additional cost.

### Practical tips for managing your account
- Use e-statements to keep records organized and accessible.
- Plan larger transfers with the daily limit of $25,000 in mind; schedule across days if needed.
- Keep an eye on your balance to maximize earnings at 0.5%.

### Quick reference
| Item | Amount |
| --- | --- |
| Monthly maintenance fee | $0.00 |
| APY | 0.5% |
| Daily digital transfer limit | $25,000 |

## Business Referral Program

Grow your network and earn rewards by referring other businesses to Navy Blue:

| Referral Detail | Value |
| --- | --- |
| Your referral bonus | $100 |
| New business welcome bonus | $75 |
| Maximum referrals per year | 10 |
| Required qualifying deposit | $5,000 |
| Deposit must be made within | 90 days |
| Your account age requirement | 60 days |

To qualify: The referred business must open a Navy Blue account and deposit at least $5,000 within 90 days of account opening. Referrer eligibility requires having been a Rho-Bank checking customer for 60 days or more.

7. Internal: Business Checking Account Promotion - November 2025
   ID: doc_bank_accounts_bank_accounts_(general)_013
   Score: 16.3378
   Content: PROMOTION NOTICE - ACTIVE FROM 11/01/2025 TO 11/30/2025: When recommending business checking accounts to customers, if multiple accounts meet all of the customer's stated requirements, agents should prioritize recommending accounts in the following order: (1) Sky Blue account should be recommended first, as it is currently under promotional priority; (2) Lime Green account should be recommended second, as it is also under promotional priority; (3) All other qualifying accounts may be recommended only if neither Sky Blue nor Lime Green meet the customer's requirements. This promotion is designed to increase adoption of our startup and premium business offerings. Always ensure the recommended account still meets ALL of the customer's stated requirements - do not recommend a promotional account if it does not satisfy the customer's needs.

8. Earning Interest on Your World Blue Balance
   ID: doc_business_checking_accounts_world_blue_007
   Score: 16.1228
   Content: ## Rate and compounding
- Your USD balance earns an Annual Percentage Yield of 1.0%
- Interest is compounded daily

## How interest is applied
- Interest accrues on eligible USD funds held in the account and is credited in accordance with your statement cycle
- If you move funds between currencies, only USD balances accrue interest at 1.0%

## Monitoring your earnings
- Track accrued and credited interest in your account activity and statements
- Export transaction data to reconcile interest income in your general ledger

## Tips for maximizing earned interest
- Keep operational reserves in USD when appropriate so they benefit from compounding daily
- Align conversion and payout timing with your cash needs so idle USD balances remain interest-earning as long as practicable

## Referral bonuses for World Blue members

In addition to interest earnings, you can earn rewards by referring other international businesses to World Blue:

- **Your bonus**: $300 for each successful referral
- **Their bonus**: $200 welcome bonus for the new business
- **Annual limit**: 12 referral bonuses per calendar year

Referral bonuses are typically credited within 7-10 business days of qualification. Both accounts must remain in good standing for bonuses to be paid.


9. Cobalt Blue: Payments and Transfers Explained
   ID: doc_business_checking_accounts_cobalt_blue_005
   Score: 15.2740
   Content: ## ACH transfers
- Standard ACH transfers are available with no fee
- Same-day ACH transfers are available with a fee of $0.00
- Submission and approval cutoffs apply for same-day processing; initiate early to improve the likelihood of same-day delivery

## Domestic wire transfers
- Outgoing domestic wire transfer fee: $20.00
- Use wires when you need confirmed, rapid delivery to U.S. financial institutions

## Incoming wires
- You get 5 incoming domestic wire transfers per month at no charge
- Additional incoming domestic wires beyond this included amount may incur a fee

## Choosing the right method
- Prefer ACH for routine payments where timing is flexible
- Use same-day ACH when faster delivery is needed at the same-day ACH timetable
- Select domestic wires for time-sensitive or high-assurance payments

## Tracking and confirmations
- Review transfer status in your activity feed
- Save beneficiary details to reduce entry errors and speed up future payments

## Referral bonus requirements
If you're referring another business to Cobalt Blue, here are the qualification details:
- Qualifying deposit: The referred business must deposit at least $7,500 to trigger the referral bonus
- Time window: This deposit must be made within 90 days of account opening
- Your eligibility: To participate, your earliest-opened Rho-Bank checking account must have reached 60 days of age.

10. How to transition a Light Green Account to Blue or Green Account (checking)
   ID: doc_checking_accounts_light_green_account_010
   Score: 15.0255
   Content: ## Determine if the change is automatic
- If Yes is True, your account will convert to an eligible adult checking option automatically at the appropriate time.

## If the change is not automatic
- If Yes is False, initiate a move to Blue or Green Account (checking) by submitting an upgrade request and selecting your preferred account type.

### Before you switch
- Compare features and fees of Blue and Green Account (checking) to choose the best fit.
- Confirm that any scheduled payments or deposits will continue without interruption after the transition.


[Timing: retrieval=3ms, reranking=0ms, total=3ms]

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "id": "skill-5",
  "role": "tool",
  "requestor": "assistant",
  "error": false,
  "turn_idx": 11,
  "timestamp": "2026-11-15T01:52:35.233695"
}
```


</details>

<a id="m012"></a>

### M012 · assistant

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "skill-6",
      "name": "KB_search",
      "arguments": {
        "query": "get_referral_link checking account submit referral user"
      },
      "requestor": "assistant"
    }
  ],
  "is_audio": false,
  "turn_idx": 12,
  "timestamp": "2026-11-15T01:52:35.245008",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 0.010788296000100672,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m013"></a>

### M013 · tool

1. Internal: Checking Account Referral Program Terms and Restrictions
   ID: doc_bank_accounts_bank_accounts_(general)_047
   Score: 14.1837
   Content: ## Program overview
Each checking account type has its own referral bonus amounts and qualification requirements. This document covers the general terms and restrictions that apply to all checking account referral programs. Before giving any recommendations or information on referral terms, you must check that the user is eligible to submit referrals first, as users who are not eligible to submit referrals while being given recommendations by the agent tend to leave dissatisfactory reviews. 

## Rolling window limit
- You can receive at most 2 referral bonuses in any rolling 9-day window.
- If you attempt to receive more than 2 referrals in a single 9-day period, the third referral (and any subsequent referrals in that window) will be automatically denied.
- This limit applies across all checking account types; referrals from different accounts count toward the same 9-day cap.
- A rolling 9-day window means the count is evaluated based on the exact timestamps of your most recent referral bonuses, not calendar weeks.
- Auto-denied referrals due to the limit cannot be reinstated within the same 9-day window.

## Eligibility restrictions
- The referred person must be a new Rho-Bank customer with no existing checking, savings, or closed accounts within the past 12 months.
- The referrer and referred person cannot be registered at the same address.
- The referred person must be 18 years or older, except for the Light Green Account which allows minors with a guardian.
- For business accounts: The referred business must have a different primary owner than any existing Rho-Bank business account, based on the SSN of the primary authorized signer.

## Referrer tenure policy
- Every referral program requires the referrer to meet a tenure threshold before participating.
- This threshold is calculated from when you first became a Rho-Bank checking customer—specifically, the date your earliest checking account was opened.
- The type of account you currently hold is irrelevant to this calculation. Whether you have a basic or premium product, the tenure measurement remains the same.
- Consequently, holding one account type does not prevent you from referring someone to a different account type, as long as the duration since your first account meets or exceeds the program's stated minimum.

## Bonus conditions
- The qualifying deposit must be new money and cannot be transferred from another Rho-Bank account.
- The qualifying deposit must remain in the account for at least 30 days after the qualifying period ends.
- If the referred account is closed within 90 days of opening, the referral bonus may be reversed (clawback provision).

## Stacking restrictions
- The referral bonus cannot be combined with other new account promotions or sign-up bonuses.
- Only one referral code can be applied per new account.

## Referral status definitions
- COMPLETE — The referred person has successfully opened a new account and met the criteria to receive the referral bonus.
- IN_PROGRESS — The referred person has successfully opened a new account and is working toward meeting the qualifying deposit requirement.
- NO_PROGRESS — The referred person has not applied yet; no progress has been made.
- APPLIED — The referred person has submitted an application and is awaiting a decision.
- REJECTED — The referral has been denied (e.g., rolling window limit exceeded, ineligible referral).
- ERROR — A system error occurred during the referral process.

## Practical guidance
- Track the timing of your last two successful referral bonuses before sending additional referrals.
- If a referral is denied for hitting the rolling window limit, wait until enough time has passed to drop under the cap before attempting another.
- Both accounts must remain in good standing for bonuses to be paid.

2. FAQ: Checking Account Referrals
   ID: doc_bank_accounts_bank_accounts_(general)_048
   Score: 10.7859
   Content: ## Frequently asked questions about checking account referrals

### How many people can I refer at once?
You can have multiple referrals in progress, but you can only receive a maximum of 2 referral bonuses in any rolling 9-day window. If you exceed this limit, additional referrals will be automatically denied until enough time passes.

### Can I refer someone who used to have a Rho-Bank account?
No. The referred person must be a new Rho-Bank customer with no existing or closed accounts within the past 12 months. Former customers must wait 12 months after their last account closure before being eligible as a referral.

### Can I refer someone who lives at the same address as me?
No. The referrer and referred person cannot be registered at the same address. This restriction helps prevent abuse of the referral program.

### What counts as a qualifying deposit?
The qualifying deposit must be new money brought into Rho-Bank. Transfers from another Rho-Bank account do not count. The deposit can come from an external bank transfer, direct deposit, mobile check deposit, or cash/check deposit at a branch.

### What happens if the person I referred closes their account early?
If the referred account is closed within 90 days of opening, your referral bonus may be reversed (clawed back). Both accounts must remain in good standing for bonuses to be retained.

### Can I combine the referral bonus with other promotions?
No. The referral bonus cannot be combined with other new account promotions or sign-up bonuses. Only one promotional offer can be applied per new account.

### What do the referral statuses mean?
- **COMPLETE**: The referral was successful and bonuses will be paid.
- **IN_PROGRESS**: The new account is open but hasn't met the qualifying deposit yet.
- **NO_PROGRESS**: The referred person hasn't started an application.
- **APPLIED**: An application has been submitted and is being reviewed.
- **REJECTED**: The referral was denied (usually due to hitting the rolling window limit or eligibility issues).
- **ERROR**: A system error occurred; try again later or contact support.

### Why was my referral rejected?
Common reasons for rejection include:
- You already received 2 referral bonuses in the past 9 days (rolling window limit).
- The referred person already has or recently had a Rho-Bank account.
- You and the referred person are registered at the same address.
- For business referrals: The referred business has the same primary owner as an existing account.

### How long do I have to wait after a rejection to refer again?
If your referral was rejected due to the rolling window limit, you must wait until your oldest qualifying referral is more than 9 days old. The limit is based on a rolling window, so you become eligible again as older referrals age out.

### Can I refer someone for a business checking account?
Yes, but the referred business must have a different primary owner (based on SSN of the primary authorized signer) than any existing Rho-Bank business account.

### Do I need to have the same account type to refer someone for it?
No. Referrer eligibility hinges on how long you've been a Rho-Bank checking customer, not which product you currently use. The tenure threshold is measured from when you opened your very first checking account with us. Someone with a Navy Blue account can refer others for World Blue, True Blue, or any other checking product—provided they've met the duration requirement.

### How long does the referred person have to make the qualifying deposit?
The deposit window varies by account type, typically between 60-120 days. Check the specific account's referral terms for the exact timeframe. After the deposit is made, it must remain in the account for at least 30 additional days.

3. Getting Started with Sky Blue: Startup Account Setup
   ID: doc_business_checking_accounts_sky_blue_001
   Score: 10.6333
   Content: ## Verify Eligibility
- Confirm your company is within 4 years of formation.
- Check whether you meet the funding requirement: 0.

## Understand Key Cost Terms Before You Apply
- Your startup receives a free period of 6 months.
- After the free period, the monthly maintenance fee is $25.00.
- If your balance goes negative, the overdraft fee is $0.00.

## Prepare Your Application
- Gather company formation documents and ownership details.
- Be ready to provide basic business information and authorized signers.
- Plan initial account settings, such as user permissions and card controls, so you can activate quickly after approval.

## Submit and Configure
- Complete the online application and upload requested documents.
- After approval, log in to set user roles, spending controls, and alerts.
- Link external accounts to enable seamless transfers.

## Startup Referral Program
Help other startups get started with Sky Blue:
- Your bonus: $150 for each successful referral
- Their bonus: $250 welcome bonus
- Annual limit: 8 referrals per year

## First-Funding and Go-Live Checklist
- Make an initial deposit from a linked account.
- Confirm your free period of 6 months is visible in your billing section.
- Review your fee settings to ensure you understand the transition to $25.00 and the overdraft policy of $0.00.

4. Beige Account Referral Program
   ID: doc_business_checking_accounts_beige_012
   Score: 10.4923
   Content: ## Enterprise referral program

Refer other enterprise-level businesses to the Beige Account and earn premium referral rewards.

### Premium rewards
- **Your reward**: $500 for each qualifying referral
- **Their reward**: $350 welcome bonus
- **Annual maximum**: 15 referral bonuses per calendar year

### Qualification criteria
To earn a referral bonus:
1. Referrer tenure requirement: 120 days since opening your first checking account with us.
2. The referred enterprise must open a Beige Account
3. They must deposit at least $100,000 within 120 days

### Referral details
| Detail | Amount |
|---|---|
| Referrer bonus | $500 |
| Referred bonus | $350 |
| Maximum per year | 15 |
| Required deposit | $100,000 |
| Deposit window | 120 days |
| Minimum tenure | 120 days |

### How to participate
1. Contact your dedicated relationship manager for referral materials
2. Introduce qualified enterprises to the Beige Account benefits
3. Your relationship manager can facilitate introductions and track referrals
4. Bonuses are credited after all qualification requirements are confirmed

### Enterprise considerations
- Referrals must be for new Beige Account relationships
- Both enterprises must maintain accounts in good standing
- Premium referral bonuses reflect the enterprise-level relationship value

5. Silver Zoom Card: Referral Program - Earn Rewards for Referring Logistics Businesses
   ID: doc_business_credit_cards_silver_zoom_card_011
   Score: 10.3486
   Content: ## How the referral program works
- Earn a referral bonus of $150 for each referred logistics business that is approved and meets the qualifying spend requirement
- Bonuses are capped at 10 per calendar year

## Qualifying activity for your referral
- The referred business must complete purchases totaling $7,500 within 90 days of account opening
- Only one referrer is credited per approved account

## Program timing
- No new referrals are accepted after 2025-10-01

## How to refer
- Share your referral link or submit the referral through your account portal before the referred business applies
- Ensure the referred business uses your link or is otherwise properly attributed during application
- Track referral status within your account until the qualifying spend threshold of $7,500 is met

## Payout details
- Bonuses are typically issued to the referrer after the referred business satisfies the $7,500 requirement within 90 days
- If the referred business returns purchases or does not meet the requirement, no bonus is issued

6. Internal: Understanding Credit Card Referral Statuses.
   ID: doc_credit_cards_credit_cards_(general)_001
   Score: 10.3073
   Content: ## Referral status meanings

- COMPLETE — the referred person has successfully opened a new account and met the criteria to get the referral bonus
- IN_PROGRESS — the referred person has successfully opened a new account and is in progress to meet the criteria for the referral bonus
- NO_PROGRESS — the referred person has not applied yet, no progress has been made
- APPLIED — the referred person has sent in the application and is waiting for a decision
- REJECTED — the user has too many referral processes going on
- ERROR — an error has occurred throughout the process

### How to interpret and act
- COMPLETE: The bonus will be granted per the applicable referral program terms.
- IN_PROGRESS: No action required; monitor until criteria are met.
- NO_PROGRESS: You may remind the referrer that the invitee has not started an application.
- APPLIED: Await the application decision; no manual intervention is needed.
- REJECTED: Do not retry immediately; review the user’s existing referral activity before advising next steps.
- ERROR: Retry later or escalate internally if the condition persists.

7. Light Blue Account Referral Program
   ID: doc_checking_accounts_light_blue_account_007
   Score: 10.2711
   Content: ## Earn rewards by referring friends

Share the Light Blue Account with others and earn cash bonuses.

### What you earn
- Referral bonus: $30 for each successful referral
- Maximum referrals: 5 per calendar year

### What they receive
- Welcome bonus: $20 when they open and fund their account

### Requirements

| Requirement | Detail |
|---|---|
| Qualifying deposit | $500 |
| Deposit window | Within 60 days of account opening |
| Referrer tenure | 30 days |

### How it works
1. Share your unique referral link with friends and family
2. They open a Light Blue Account using your link
3. They deposit at least $500 within 60 days
4. You receive $30 and they receive $20

### Eligibility
- To qualify as a referrer, you must have been a Rho-Bank checking account holder for 30 days or longer.
- You can earn up to 5 referral bonuses per calendar year

8. Bronze Saver Account: Adding authorized users to your account
   ID: doc_business_savings_accounts_bronze_saver_account_007
   Score: 10.2177
   Content: ## Access limits
- You can add up to 2 authorized users to your Bronze Saver Account.

## Requirements
- A linked Rho-Bank business checking account is required: Yes. Ensure the linked account remains in good standing before adding users.

## How to add users
- Navigate to your account settings and choose the authorized users option.
- Enter the user’s details, assign the appropriate access permissions, and confirm.
- The user will receive an invitation to set up access.

## Managing access
- Update or revoke user permissions from the same settings area at any time.
- Review user activity regularly to maintain proper controls.

9. Gold Years Account Referral Program
   ID: doc_checking_accounts_gold_years_account_010
   Score: 10.0607
   Content: ## Refer a friend to Gold Years

Share the benefits of the Gold Years Account with friends and family members who are 62 or older.

### Rewards
- **You receive**: $50 for each successful referral
- **They receive**: $75 as a welcome bonus
- **Annual maximum**: 6 referral bonuses per calendar year

### How to qualify
- The referrer must have maintained checking account status with Rho-Bank for 30 days.
- The person you refer must be eligible for a Gold Years Account (age 62+)
- They must deposit $1,000 within 90 days of account opening

### Referral summary
| Program element | Detail |
|---|---|
| Your bonus | $50 |
| Their bonus | $75 |
| Max referrals/year | 6 |
| Qualifying deposit | $1,000 |
| Deposit deadline | 90 days |
| Customer tenure | 30 days |

### Getting started
1. Find your personalized referral link in your account settings
2. Share it with eligible friends and family
3. Track successful referrals in your rewards dashboard

10. Green Fee-Free Account Referral Program
   ID: doc_checking_accounts_green_fee-free_account_007
   Score: 9.6725
   Content: ## Refer and earn

Help others discover the Green Fee-Free Account and earn rewards for successful referrals.

### Bonus structure
- Your reward: $20 per successful referral
- New member reward: $35 welcome bonus
- Annual limit: 4 referrals per year

### Qualification requirements
For a referral to count as successful:
- The new account holder must deposit at least $300
- This deposit must be made within 60 days of opening their account
- Your Rho-Bank checking relationship must span at least 30 days.

### Quick reference
| Detail | Amount |
|---|---|
| You earn | $20 |
| They earn | $35 |
| Max per year | 4 |
| Required deposit | $300 |
| Deposit deadline | 60 days |
| Referrer eligibility | 30 days |

### How to participate
1. Access your referral link from your account dashboard
2. Share with potential new members
3. Track your referrals and bonuses in the rewards section


[Timing: retrieval=2ms, reranking=0ms, total=2ms]

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "id": "skill-6",
  "role": "tool",
  "requestor": "assistant",
  "error": false,
  "turn_idx": 13,
  "timestamp": "2026-11-15T01:52:35.247899"
}
```


</details>

<a id="m014"></a>

### M014 · assistant

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "skill-7",
      "name": "KB_search",
      "arguments": {
        "query": "World Blue referral program qualifying deposit bonus amount"
      },
      "requestor": "assistant"
    }
  ],
  "is_audio": false,
  "turn_idx": 14,
  "timestamp": "2026-11-15T01:52:46.752222",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 11.503439328997047,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m015"></a>

### M015 · tool

1. True Blue Account: Fee Waivers and Balance Requirements
   ID: doc_business_checking_accounts_true_blue_002
   Score: 20.0797
   Content: ## Waiving your monthly maintenance fee
- You will be charged $75.00 each month unless you meet the waiver threshold.
- The monthly maintenance fee is waived when your balance is at least $50,000 during the statement period.

## Minimum balance requirement vs. fee waiver threshold
- Minimum balance requirement: $25,000 to maintain the account and access premium features.
- Fee waiver threshold: $50,000 to waive the $75.00 monthly maintenance fee.
- Falling below $25,000 may limit access to premium features until your balance is restored.

## Overdrafts and shortfalls
- If your balance goes negative, a per-occurrence overdraft fee of $25.00 may apply.

## How to avoid fees
- Maintain a balance of at least $50,000 to waive the monthly maintenance fee.
- Set internal processes to monitor balances against both $25,000 and $50,000.
- If a shortfall is anticipated, transfer funds promptly to avoid the $25.00 and preserve eligibility for the fee waiver.

## True Blue Referral Program

Refer other high-volume businesses to True Blue and earn significant rewards:

| Benefit | Amount |
| --- | --- |
| Referrer bonus | $350 per referral |
| New member bonus | $250 |
| Maximum referrals per year | 15 |
| Qualifying deposit | $50,000 |
| Deposit window | 120 days |
| Account age requirement | 90 days |

### Referral requirements
- The referred business must deposit $50,000 within 120 days of opening their True Blue account.
- Eligibility is based on how long you've been a Rho-Bank checking customer. The account age threshold is 90 days, calculated from when you opened your oldest checking account.
- Referral bonuses are paid after qualification is confirmed and are subject to the annual limit of 15.

2. Beige Account Referral Program
   ID: doc_business_checking_accounts_beige_012
   Score: 18.2371
   Content: ## Enterprise referral program

Refer other enterprise-level businesses to the Beige Account and earn premium referral rewards.

### Premium rewards
- **Your reward**: $500 for each qualifying referral
- **Their reward**: $350 welcome bonus
- **Annual maximum**: 15 referral bonuses per calendar year

### Qualification criteria
To earn a referral bonus:
1. Referrer tenure requirement: 120 days since opening your first checking account with us.
2. The referred enterprise must open a Beige Account
3. They must deposit at least $100,000 within 120 days

### Referral details
| Detail | Amount |
|---|---|
| Referrer bonus | $500 |
| Referred bonus | $350 |
| Maximum per year | 15 |
| Required deposit | $100,000 |
| Deposit window | 120 days |
| Minimum tenure | 120 days |

### How to participate
1. Contact your dedicated relationship manager for referral materials
2. Introduce qualified enterprises to the Beige Account benefits
3. Your relationship manager can facilitate introductions and track referrals
4. Bonuses are credited after all qualification requirements are confirmed

### Enterprise considerations
- Referrals must be for new Beige Account relationships
- Both enterprises must maintain accounts in good standing
- Premium referral bonuses reflect the enterprise-level relationship value

3. Navy Blue Business Checking: Complete Guide
   ID: doc_business_checking_accounts_navy_blue_001
   Score: 17.8806
   Content: ## Key Account Costs and Limits

- Monthly maintenance fee: $0.00
- Annual Percentage Yield (APY) on balances: 0.5%
- Daily digital transfer limit: $25,000

### What you can expect day to day
- No minimum balance requirement, so you can use the account flexibly.
- Unlimited digital transfers within the daily limit of $25,000.
- Optional overdraft settings are available if you want coverage on eligible transactions.
- E-statements are included at no additional cost.

### Practical tips for managing your account
- Use e-statements to keep records organized and accessible.
- Plan larger transfers with the daily limit of $25,000 in mind; schedule across days if needed.
- Keep an eye on your balance to maximize earnings at 0.5%.

### Quick reference
| Item | Amount |
| --- | --- |
| Monthly maintenance fee | $0.00 |
| APY | 0.5% |
| Daily digital transfer limit | $25,000 |

## Business Referral Program

Grow your network and earn rewards by referring other businesses to Navy Blue:

| Referral Detail | Value |
| --- | --- |
| Your referral bonus | $100 |
| New business welcome bonus | $75 |
| Maximum referrals per year | 10 |
| Required qualifying deposit | $5,000 |
| Deposit must be made within | 90 days |
| Your account age requirement | 60 days |

To qualify: The referred business must open a Navy Blue account and deposit at least $5,000 within 90 days of account opening. Referrer eligibility requires having been a Rho-Bank checking customer for 60 days or more.

4. Dark Green Account Referral Program
   ID: doc_checking_accounts_dark_green_account_010
   Score: 17.7577
   Content: ## Share the Dark Green experience

Refer others to the Dark Green Account and earn rewards when they join.

### Referral rewards
- **Your bonus**: $40 for each qualifying referral
- **Their bonus**: $30 welcome bonus
- **Maximum per year**: 6 referral bonuses

### Qualification criteria
To qualify for the referral bonus:
1. You must satisfy the 45-day minimum as a Rho-Bank checking customer.
2. The person you refer must open a Dark Green Account
3. They must deposit at least $1,000 within 60 days of opening

### Program details
| Aspect | Value |
|---|---|
| Referrer bonus | $40 |
| Referred bonus | $30 |
| Annual cap | 6 referrals |
| Minimum deposit | $1,000 |
| Deposit window | 60 days |
| Tenure required | 45 days |

### Bonus payment
- Bonuses are credited within 5-7 business days after qualification
- Both you and the new member must maintain your accounts in good standing

5. Earning Interest on Your World Blue Balance
   ID: doc_business_checking_accounts_world_blue_007
   Score: 17.6515
   Content: ## Rate and compounding
- Your USD balance earns an Annual Percentage Yield of 1.0%
- Interest is compounded daily

## How interest is applied
- Interest accrues on eligible USD funds held in the account and is credited in accordance with your statement cycle
- If you move funds between currencies, only USD balances accrue interest at 1.0%

## Monitoring your earnings
- Track accrued and credited interest in your account activity and statements
- Export transaction data to reconcile interest income in your general ledger

## Tips for maximizing earned interest
- Keep operational reserves in USD when appropriate so they benefit from compounding daily
- Align conversion and payout timing with your cash needs so idle USD balances remain interest-earning as long as practicable

## Referral bonuses for World Blue members

In addition to interest earnings, you can earn rewards by referring other international businesses to World Blue:

- **Your bonus**: $300 for each successful referral
- **Their bonus**: $200 welcome bonus for the new business
- **Annual limit**: 12 referral bonuses per calendar year

Referral bonuses are typically credited within 7-10 business days of qualification. Both accounts must remain in good standing for bonuses to be paid.


6. FAQ: Checking Account Referrals
   ID: doc_bank_accounts_bank_accounts_(general)_048
   Score: 17.5881
   Content: ## Frequently asked questions about checking account referrals

### How many people can I refer at once?
You can have multiple referrals in progress, but you can only receive a maximum of 2 referral bonuses in any rolling 9-day window. If you exceed this limit, additional referrals will be automatically denied until enough time passes.

### Can I refer someone who used to have a Rho-Bank account?
No. The referred person must be a new Rho-Bank customer with no existing or closed accounts within the past 12 months. Former customers must wait 12 months after their last account closure before being eligible as a referral.

### Can I refer someone who lives at the same address as me?
No. The referrer and referred person cannot be registered at the same address. This restriction helps prevent abuse of the referral program.

### What counts as a qualifying deposit?
The qualifying deposit must be new money brought into Rho-Bank. Transfers from another Rho-Bank account do not count. The deposit can come from an external bank transfer, direct deposit, mobile check deposit, or cash/check deposit at a branch.

### What happens if the person I referred closes their account early?
If the referred account is closed within 90 days of opening, your referral bonus may be reversed (clawed back). Both accounts must remain in good standing for bonuses to be retained.

### Can I combine the referral bonus with other promotions?
No. The referral bonus cannot be combined with other new account promotions or sign-up bonuses. Only one promotional offer can be applied per new account.

### What do the referral statuses mean?
- **COMPLETE**: The referral was successful and bonuses will be paid.
- **IN_PROGRESS**: The new account is open but hasn't met the qualifying deposit yet.
- **NO_PROGRESS**: The referred person hasn't started an application.
- **APPLIED**: An application has been submitted and is being reviewed.
- **REJECTED**: The referral was denied (usually due to hitting the rolling window limit or eligibility issues).
- **ERROR**: A system error occurred; try again later or contact support.

### Why was my referral rejected?
Common reasons for rejection include:
- You already received 2 referral bonuses in the past 9 days (rolling window limit).
- The referred person already has or recently had a Rho-Bank account.
- You and the referred person are registered at the same address.
- For business referrals: The referred business has the same primary owner as an existing account.

### How long do I have to wait after a rejection to refer again?
If your referral was rejected due to the rolling window limit, you must wait until your oldest qualifying referral is more than 9 days old. The limit is based on a rolling window, so you become eligible again as older referrals age out.

### Can I refer someone for a business checking account?
Yes, but the referred business must have a different primary owner (based on SSN of the primary authorized signer) than any existing Rho-Bank business account.

### Do I need to have the same account type to refer someone for it?
No. Referrer eligibility hinges on how long you've been a Rho-Bank checking customer, not which product you currently use. The tenure threshold is measured from when you opened your very first checking account with us. Someone with a Navy Blue account can refer others for World Blue, True Blue, or any other checking product—provided they've met the duration requirement.

### How long does the referred person have to make the qualifying deposit?
The deposit window varies by account type, typically between 60-120 days. Check the specific account's referral terms for the exact timeframe. After the deposit is made, it must remain in the account for at least 30 additional days.

7. Gold Years Account Referral Program
   ID: doc_checking_accounts_gold_years_account_010
   Score: 17.1384
   Content: ## Refer a friend to Gold Years

Share the benefits of the Gold Years Account with friends and family members who are 62 or older.

### Rewards
- **You receive**: $50 for each successful referral
- **They receive**: $75 as a welcome bonus
- **Annual maximum**: 6 referral bonuses per calendar year

### How to qualify
- The referrer must have maintained checking account status with Rho-Bank for 30 days.
- The person you refer must be eligible for a Gold Years Account (age 62+)
- They must deposit $1,000 within 90 days of account opening

### Referral summary
| Program element | Detail |
|---|---|
| Your bonus | $50 |
| Their bonus | $75 |
| Max referrals/year | 6 |
| Qualifying deposit | $1,000 |
| Deposit deadline | 90 days |
| Customer tenure | 30 days |

### Getting started
1. Find your personalized referral link in your account settings
2. Share it with eligible friends and family
3. Track successful referrals in your rewards dashboard

8. Silver Zoom Card: Referral Program - Earn Rewards for Referring Logistics Businesses
   ID: doc_business_credit_cards_silver_zoom_card_011
   Score: 17.0723
   Content: ## How the referral program works
- Earn a referral bonus of $150 for each referred logistics business that is approved and meets the qualifying spend requirement
- Bonuses are capped at 10 per calendar year

## Qualifying activity for your referral
- The referred business must complete purchases totaling $7,500 within 90 days of account opening
- Only one referrer is credited per approved account

## Program timing
- No new referrals are accepted after 2025-10-01

## How to refer
- Share your referral link or submit the referral through your account portal before the referred business applies
- Ensure the referred business uses your link or is otherwise properly attributed during application
- Track referral status within your account until the qualifying spend threshold of $7,500 is met

## Payout details
- Bonuses are typically issued to the referrer after the referred business satisfies the $7,500 requirement within 90 days
- If the referred business returns purchases or does not meet the requirement, no bonus is issued

9. Business Silver Rewards Card: Referral Program - Earn Rewards for Referring Businesses
   ID: doc_business_credit_cards_business_silver_rewards_card_013
   Score: 16.6868
   Content: ## What you can earn
- Earn $100 for each successful referral that is approved and meets the qualifying spend requirement
- You can earn up to 10 referral bonuses per calendar year

## Qualifying spend requirement
- The referred business must spend at least $3,000 within 90 days of account opening for you to receive the bonus

## How to refer
- Share a referral through the official referral channel so applications are tracked correctly
- Ensure the referred business uses your referral details when applying

## Tracking and payout
- After the referred business is approved and completes the qualifying spend, your $100 bonus will be processed according to program rules
- If a referral does not appear, contact support with the referred business name and application date so it can be investigated

10. Business Gold Rewards Card: Referral Program - Earn Rewards for Referring Businesses
   ID: doc_business_credit_cards_business_gold_rewards_card_010
   Score: 16.3871
   Content: ## How the Referral Bonus Works
- Earn $200 for each successful referral who is approved and meets the qualifying spend.
- You can earn up to 8 referral bonuses per calendar year.

## Qualifying Spend Requirement
- The referred business must spend $7,500 within 90 from account opening to qualify your bonus.

## Program Timeline
- The referral program accepts new referrals until 2025-09-15. Referrals submitted after this date are not eligible.

## How to Refer
- Generate your unique referral link from your account’s referral center.
- Share the link directly with businesses that consent to receive it.
- Track application status and eligibility in the referral dashboard.

## Payouts
- Once the referred account is approved and completes $7,500 within 90, your $200 is queued for issuance to your account.

## Rules and Best Practices
- Self-referrals are not permitted.
- Share referral invitations only with contacts who have given permission to receive them.
- If a referral applies without your link, the referral may not be attributed.
- Program terms, eligible industries, and promotional availability may change without notice prior to 2025-09-15.


[Timing: retrieval=2ms, reranking=0ms, total=2ms]

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "id": "skill-7",
  "role": "tool",
  "requestor": "assistant",
  "error": false,
  "turn_idx": 15,
  "timestamp": "2026-11-15T01:52:46.754936"
}
```


</details>

<a id="m016"></a>

### M016 · assistant

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "skill-8",
      "name": "KB_search",
      "arguments": {
        "query": "Cobalt Blue referral bonus amount how much earn"
      },
      "requestor": "assistant"
    }
  ],
  "is_audio": false,
  "turn_idx": 16,
  "timestamp": "2026-11-15T01:52:46.763470",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 0.007284477993380278,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m017"></a>

### M017 · tool

1. True Blue Account: Fee Waivers and Balance Requirements
   ID: doc_business_checking_accounts_true_blue_002
   Score: 14.9732
   Content: ## Waiving your monthly maintenance fee
- You will be charged $75.00 each month unless you meet the waiver threshold.
- The monthly maintenance fee is waived when your balance is at least $50,000 during the statement period.

## Minimum balance requirement vs. fee waiver threshold
- Minimum balance requirement: $25,000 to maintain the account and access premium features.
- Fee waiver threshold: $50,000 to waive the $75.00 monthly maintenance fee.
- Falling below $25,000 may limit access to premium features until your balance is restored.

## Overdrafts and shortfalls
- If your balance goes negative, a per-occurrence overdraft fee of $25.00 may apply.

## How to avoid fees
- Maintain a balance of at least $50,000 to waive the monthly maintenance fee.
- Set internal processes to monitor balances against both $25,000 and $50,000.
- If a shortfall is anticipated, transfer funds promptly to avoid the $25.00 and preserve eligibility for the fee waiver.

## True Blue Referral Program

Refer other high-volume businesses to True Blue and earn significant rewards:

| Benefit | Amount |
| --- | --- |
| Referrer bonus | $350 per referral |
| New member bonus | $250 |
| Maximum referrals per year | 15 |
| Qualifying deposit | $50,000 |
| Deposit window | 120 days |
| Account age requirement | 90 days |

### Referral requirements
- The referred business must deposit $50,000 within 120 days of opening their True Blue account.
- Eligibility is based on how long you've been a Rho-Bank checking customer. The account age threshold is 90 days, calculated from when you opened your oldest checking account.
- Referral bonuses are paid after qualification is confirmed and are subject to the annual limit of 15.

2. Light Blue Account Referral Program
   ID: doc_checking_accounts_light_blue_account_007
   Score: 14.2217
   Content: ## Earn rewards by referring friends

Share the Light Blue Account with others and earn cash bonuses.

### What you earn
- Referral bonus: $30 for each successful referral
- Maximum referrals: 5 per calendar year

### What they receive
- Welcome bonus: $20 when they open and fund their account

### Requirements

| Requirement | Detail |
|---|---|
| Qualifying deposit | $500 |
| Deposit window | Within 60 days of account opening |
| Referrer tenure | 30 days |

### How it works
1. Share your unique referral link with friends and family
2. They open a Light Blue Account using your link
3. They deposit at least $500 within 60 days
4. You receive $30 and they receive $20

### Eligibility
- To qualify as a referrer, you must have been a Rho-Bank checking account holder for 30 days or longer.
- You can earn up to 5 referral bonuses per calendar year

3. FAQ: Blue Account
   ID: doc_checking_accounts_blue_account_010
   Score: 13.4504
   Content: ## Frequently asked questions

### What does a paper statement cost?
Paper statements are available for $2.50 per month.

### What APY do I earn on my balance?
Your Blue Account earns 0.01% APY on balances.

### Can I set low-balance alerts?
Yes. You can enable alerts at a threshold such as $62 so you are notified when your available balance reaches that level.

### How long do external bank transfers take?
Transfers to another bank typically complete in 2 business days.

### What happens if a deposited check is returned unpaid?
If a deposited check is returned by the issuing bank, a returned deposit fee of $15.00 applies.

### Is there a fee to receive a domestic wire?
Yes. Incoming domestic wires are assessed a fee of $12.50 per wire.

### Does the Blue Account have a referral program?
Yes. When you refer someone to open a Blue Account, you earn $35 for each successful referral. The person you refer receives $30 as a welcome bonus.

### What are the requirements for the referral bonus?
The referred person must deposit at least $500 within 60 days of opening their account. A minimum banking relationship of 30 days is required to participate—this is measured from when you first opened any checking account with us.

### Is there a limit to how many referral bonuses I can earn?
Yes. You can earn up to 5 referral bonuses per calendar year.

4. Beige Account Referral Program
   ID: doc_business_checking_accounts_beige_012
   Score: 13.0130
   Content: ## Enterprise referral program

Refer other enterprise-level businesses to the Beige Account and earn premium referral rewards.

### Premium rewards
- **Your reward**: $500 for each qualifying referral
- **Their reward**: $350 welcome bonus
- **Annual maximum**: 15 referral bonuses per calendar year

### Qualification criteria
To earn a referral bonus:
1. Referrer tenure requirement: 120 days since opening your first checking account with us.
2. The referred enterprise must open a Beige Account
3. They must deposit at least $100,000 within 120 days

### Referral details
| Detail | Amount |
|---|---|
| Referrer bonus | $500 |
| Referred bonus | $350 |
| Maximum per year | 15 |
| Required deposit | $100,000 |
| Deposit window | 120 days |
| Minimum tenure | 120 days |

### How to participate
1. Contact your dedicated relationship manager for referral materials
2. Introduce qualified enterprises to the Beige Account benefits
3. Your relationship manager can facilitate introductions and track referrals
4. Bonuses are credited after all qualification requirements are confirmed

### Enterprise considerations
- Referrals must be for new Beige Account relationships
- Both enterprises must maintain accounts in good standing
- Premium referral bonuses reflect the enterprise-level relationship value

5. Green Fee-Free Account Referral Program
   ID: doc_checking_accounts_green_fee-free_account_007
   Score: 12.6999
   Content: ## Refer and earn

Help others discover the Green Fee-Free Account and earn rewards for successful referrals.

### Bonus structure
- Your reward: $20 per successful referral
- New member reward: $35 welcome bonus
- Annual limit: 4 referrals per year

### Qualification requirements
For a referral to count as successful:
- The new account holder must deposit at least $300
- This deposit must be made within 60 days of opening their account
- Your Rho-Bank checking relationship must span at least 30 days.

### Quick reference
| Detail | Amount |
|---|---|
| You earn | $20 |
| They earn | $35 |
| Max per year | 4 |
| Required deposit | $300 |
| Deposit deadline | 60 days |
| Referrer eligibility | 30 days |

### How to participate
1. Access your referral link from your account dashboard
2. Share with potential new members
3. Track your referrals and bonuses in the rewards section

6. Business Silver Rewards Card: Referral Program - Earn Rewards for Referring Businesses
   ID: doc_business_credit_cards_business_silver_rewards_card_013
   Score: 12.5514
   Content: ## What you can earn
- Earn $100 for each successful referral that is approved and meets the qualifying spend requirement
- You can earn up to 10 referral bonuses per calendar year

## Qualifying spend requirement
- The referred business must spend at least $3,000 within 90 days of account opening for you to receive the bonus

## How to refer
- Share a referral through the official referral channel so applications are tracked correctly
- Ensure the referred business uses your referral details when applying

## Tracking and payout
- After the referred business is approved and completes the qualifying spend, your $100 bonus will be processed according to program rules
- If a referral does not appear, contact support with the referred business name and application date so it can be investigated

7. Earning Interest on Your World Blue Balance
   ID: doc_business_checking_accounts_world_blue_007
   Score: 12.4685
   Content: ## Rate and compounding
- Your USD balance earns an Annual Percentage Yield of 1.0%
- Interest is compounded daily

## How interest is applied
- Interest accrues on eligible USD funds held in the account and is credited in accordance with your statement cycle
- If you move funds between currencies, only USD balances accrue interest at 1.0%

## Monitoring your earnings
- Track accrued and credited interest in your account activity and statements
- Export transaction data to reconcile interest income in your general ledger

## Tips for maximizing earned interest
- Keep operational reserves in USD when appropriate so they benefit from compounding daily
- Align conversion and payout timing with your cash needs so idle USD balances remain interest-earning as long as practicable

## Referral bonuses for World Blue members

In addition to interest earnings, you can earn rewards by referring other international businesses to World Blue:

- **Your bonus**: $300 for each successful referral
- **Their bonus**: $200 welcome bonus for the new business
- **Annual limit**: 12 referral bonuses per calendar year

Referral bonuses are typically credited within 7-10 business days of qualification. Both accounts must remain in good standing for bonuses to be paid.


8. Cobalt Blue: Payments and Transfers Explained
   ID: doc_business_checking_accounts_cobalt_blue_005
   Score: 12.3891
   Content: ## ACH transfers
- Standard ACH transfers are available with no fee
- Same-day ACH transfers are available with a fee of $0.00
- Submission and approval cutoffs apply for same-day processing; initiate early to improve the likelihood of same-day delivery

## Domestic wire transfers
- Outgoing domestic wire transfer fee: $20.00
- Use wires when you need confirmed, rapid delivery to U.S. financial institutions

## Incoming wires
- You get 5 incoming domestic wire transfers per month at no charge
- Additional incoming domestic wires beyond this included amount may incur a fee

## Choosing the right method
- Prefer ACH for routine payments where timing is flexible
- Use same-day ACH when faster delivery is needed at the same-day ACH timetable
- Select domestic wires for time-sensitive or high-assurance payments

## Tracking and confirmations
- Review transfer status in your activity feed
- Save beneficiary details to reduce entry errors and speed up future payments

## Referral bonus requirements
If you're referring another business to Cobalt Blue, here are the qualification details:
- Qualifying deposit: The referred business must deposit at least $7,500 to trigger the referral bonus
- Time window: This deposit must be made within 90 days of account opening
- Your eligibility: To participate, your earliest-opened Rho-Bank checking account must have reached 60 days of age.

9. Navy Blue Business Checking: Complete Guide
   ID: doc_business_checking_accounts_navy_blue_001
   Score: 12.3868
   Content: ## Key Account Costs and Limits

- Monthly maintenance fee: $0.00
- Annual Percentage Yield (APY) on balances: 0.5%
- Daily digital transfer limit: $25,000

### What you can expect day to day
- No minimum balance requirement, so you can use the account flexibly.
- Unlimited digital transfers within the daily limit of $25,000.
- Optional overdraft settings are available if you want coverage on eligible transactions.
- E-statements are included at no additional cost.

### Practical tips for managing your account
- Use e-statements to keep records organized and accessible.
- Plan larger transfers with the daily limit of $25,000 in mind; schedule across days if needed.
- Keep an eye on your balance to maximize earnings at 0.5%.

### Quick reference
| Item | Amount |
| --- | --- |
| Monthly maintenance fee | $0.00 |
| APY | 0.5% |
| Daily digital transfer limit | $25,000 |

## Business Referral Program

Grow your network and earn rewards by referring other businesses to Navy Blue:

| Referral Detail | Value |
| --- | --- |
| Your referral bonus | $100 |
| New business welcome bonus | $75 |
| Maximum referrals per year | 10 |
| Required qualifying deposit | $5,000 |
| Deposit must be made within | 90 days |
| Your account age requirement | 60 days |

To qualify: The referred business must open a Navy Blue account and deposit at least $5,000 within 90 days of account opening. Referrer eligibility requires having been a Rho-Bank checking customer for 60 days or more.

10. Evergreen Account at a glance
   ID: doc_checking_accounts_evergreen_account_001
   Score: 11.9809
   Content: ## Key highlights
- One tree planted for every $750 you spend with your debit card
- Automatic carbon offset on purchases: $1.25 g CO2 per $1 spent
- Earn 0.05% APY on your checking balance
- Extra rewards at partner eco-friendly brands: +1.75% cashback
- Early direct deposit: get your paycheck up to 2 days early
- Mobile check deposit daily limit: $3,500

### Linked savings boosts
- Link a Green Account (savings): +0.55% APY boost
- Link a Diamond Elite Savings Account: +0.15% APY boost

### How tree planting works (at a glance)
- For every $750 in eligible spending, we plant one tree on your behalf.
- Example: Spend $750 → 1 tree planted; spend 5× that amount → 5 trees planted.

### Foreign ATM withdrawals
- Foreign ATM withdrawal fee: 2% of the withdrawal amount, with a minimum of $3.00 per transaction.
- Third-party ATM operator fees may also apply.

### Refer and grow the green community
- Refer others to join Evergreen and earn $35 per successful referral
- New members receive $25 as a welcome bonus
- Earn up to 6 referral bonuses per calendar year

## Quick reference
| Feature | Amount |
|---|---|
| Tree planting threshold | $750 per tree |
| Carbon offset rate | $1.25 g per $1 |
| Checking APY | 0.05% |
| Eco brand cashback bonus | +1.75% |
| Early direct deposit | Up to 2 days early |
| Mobile deposit daily limit | $3,500 |
| Foreign ATM withdrawal fee | 2% (min $3.00) |
| Green Savings APY boost | +0.55% |
| Diamond Elite Savings APY boost | +0.15% |
| Referral bonus (you earn) | $35 |
| Referral bonus (they receive) | $25 |
| Max referrals per year | 6 |


[Timing: retrieval=2ms, reranking=0ms, total=2ms]

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "id": "skill-8",
  "role": "tool",
  "requestor": "assistant",
  "error": false,
  "turn_idx": 17,
  "timestamp": "2026-11-15T01:52:46.767257"
}
```


</details>

<a id="m018"></a>

### M018 · assistant

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "skill-9",
      "name": "KB_search",
      "arguments": {
        "query": "Sky Blue referral program qualifying deposit details startup"
      },
      "requestor": "assistant"
    }
  ],
  "is_audio": false,
  "turn_idx": 18,
  "timestamp": "2026-11-15T01:52:46.776088",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 0.00789186600013636,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m019"></a>

### M019 · tool

1. Internal: Business Checking Account Promotion - November 2025
   ID: doc_bank_accounts_bank_accounts_(general)_013
   Score: 23.6154
   Content: PROMOTION NOTICE - ACTIVE FROM 11/01/2025 TO 11/30/2025: When recommending business checking accounts to customers, if multiple accounts meet all of the customer's stated requirements, agents should prioritize recommending accounts in the following order: (1) Sky Blue account should be recommended first, as it is currently under promotional priority; (2) Lime Green account should be recommended second, as it is also under promotional priority; (3) All other qualifying accounts may be recommended only if neither Sky Blue nor Lime Green meet the customer's requirements. This promotion is designed to increase adoption of our startup and premium business offerings. Always ensure the recommended account still meets ALL of the customer's stated requirements - do not recommend a promotional account if it does not satisfy the customer's needs.

2. Getting Started with Sky Blue: Startup Account Setup
   ID: doc_business_checking_accounts_sky_blue_001
   Score: 20.7025
   Content: ## Verify Eligibility
- Confirm your company is within 4 years of formation.
- Check whether you meet the funding requirement: 0.

## Understand Key Cost Terms Before You Apply
- Your startup receives a free period of 6 months.
- After the free period, the monthly maintenance fee is $25.00.
- If your balance goes negative, the overdraft fee is $0.00.

## Prepare Your Application
- Gather company formation documents and ownership details.
- Be ready to provide basic business information and authorized signers.
- Plan initial account settings, such as user permissions and card controls, so you can activate quickly after approval.

## Submit and Configure
- Complete the online application and upload requested documents.
- After approval, log in to set user roles, spending controls, and alerts.
- Link external accounts to enable seamless transfers.

## Startup Referral Program
Help other startups get started with Sky Blue:
- Your bonus: $150 for each successful referral
- Their bonus: $250 welcome bonus
- Annual limit: 8 referrals per year

## First-Funding and Go-Live Checklist
- Make an initial deposit from a linked account.
- Confirm your free period of 6 months is visible in your billing section.
- Review your fee settings to ensure you understand the transition to $25.00 and the overdraft policy of $0.00.

3. True Blue Account: Fee Waivers and Balance Requirements
   ID: doc_business_checking_accounts_true_blue_002
   Score: 16.6091
   Content: ## Waiving your monthly maintenance fee
- You will be charged $75.00 each month unless you meet the waiver threshold.
- The monthly maintenance fee is waived when your balance is at least $50,000 during the statement period.

## Minimum balance requirement vs. fee waiver threshold
- Minimum balance requirement: $25,000 to maintain the account and access premium features.
- Fee waiver threshold: $50,000 to waive the $75.00 monthly maintenance fee.
- Falling below $25,000 may limit access to premium features until your balance is restored.

## Overdrafts and shortfalls
- If your balance goes negative, a per-occurrence overdraft fee of $25.00 may apply.

## How to avoid fees
- Maintain a balance of at least $50,000 to waive the monthly maintenance fee.
- Set internal processes to monitor balances against both $25,000 and $50,000.
- If a shortfall is anticipated, transfer funds promptly to avoid the $25.00 and preserve eligibility for the fee waiver.

## True Blue Referral Program

Refer other high-volume businesses to True Blue and earn significant rewards:

| Benefit | Amount |
| --- | --- |
| Referrer bonus | $350 per referral |
| New member bonus | $250 |
| Maximum referrals per year | 15 |
| Qualifying deposit | $50,000 |
| Deposit window | 120 days |
| Account age requirement | 90 days |

### Referral requirements
- The referred business must deposit $50,000 within 120 days of opening their True Blue account.
- Eligibility is based on how long you've been a Rho-Bank checking customer. The account age threshold is 90 days, calculated from when you opened your oldest checking account.
- Referral bonuses are paid after qualification is confirmed and are subject to the annual limit of 15.

4. Light Blue Account Referral Program
   ID: doc_checking_accounts_light_blue_account_007
   Score: 16.2697
   Content: ## Earn rewards by referring friends

Share the Light Blue Account with others and earn cash bonuses.

### What you earn
- Referral bonus: $30 for each successful referral
- Maximum referrals: 5 per calendar year

### What they receive
- Welcome bonus: $20 when they open and fund their account

### Requirements

| Requirement | Detail |
|---|---|
| Qualifying deposit | $500 |
| Deposit window | Within 60 days of account opening |
| Referrer tenure | 30 days |

### How it works
1. Share your unique referral link with friends and family
2. They open a Light Blue Account using your link
3. They deposit at least $500 within 60 days
4. You receive $30 and they receive $20

### Eligibility
- To qualify as a referrer, you must have been a Rho-Bank checking account holder for 30 days or longer.
- You can earn up to 5 referral bonuses per calendar year

5. Silver Zoom Card: Referral Program - Earn Rewards for Referring Logistics Businesses
   ID: doc_business_credit_cards_silver_zoom_card_011
   Score: 15.1717
   Content: ## How the referral program works
- Earn a referral bonus of $150 for each referred logistics business that is approved and meets the qualifying spend requirement
- Bonuses are capped at 10 per calendar year

## Qualifying activity for your referral
- The referred business must complete purchases totaling $7,500 within 90 days of account opening
- Only one referrer is credited per approved account

## Program timing
- No new referrals are accepted after 2025-10-01

## How to refer
- Share your referral link or submit the referral through your account portal before the referred business applies
- Ensure the referred business uses your link or is otherwise properly attributed during application
- Track referral status within your account until the qualifying spend threshold of $7,500 is met

## Payout details
- Bonuses are typically issued to the referrer after the referred business satisfies the $7,500 requirement within 90 days
- If the referred business returns purchases or does not meet the requirement, no bonus is issued

6. Dark Green Account Referral Program
   ID: doc_checking_accounts_dark_green_account_010
   Score: 15.0465
   Content: ## Share the Dark Green experience

Refer others to the Dark Green Account and earn rewards when they join.

### Referral rewards
- **Your bonus**: $40 for each qualifying referral
- **Their bonus**: $30 welcome bonus
- **Maximum per year**: 6 referral bonuses

### Qualification criteria
To qualify for the referral bonus:
1. You must satisfy the 45-day minimum as a Rho-Bank checking customer.
2. The person you refer must open a Dark Green Account
3. They must deposit at least $1,000 within 60 days of opening

### Program details
| Aspect | Value |
|---|---|
| Referrer bonus | $40 |
| Referred bonus | $30 |
| Annual cap | 6 referrals |
| Minimum deposit | $1,000 |
| Deposit window | 60 days |
| Tenure required | 45 days |

### Bonus payment
- Bonuses are credited within 5-7 business days after qualification
- Both you and the new member must maintain your accounts in good standing

7. Beige Account Referral Program
   ID: doc_business_checking_accounts_beige_012
   Score: 14.8265
   Content: ## Enterprise referral program

Refer other enterprise-level businesses to the Beige Account and earn premium referral rewards.

### Premium rewards
- **Your reward**: $500 for each qualifying referral
- **Their reward**: $350 welcome bonus
- **Annual maximum**: 15 referral bonuses per calendar year

### Qualification criteria
To earn a referral bonus:
1. Referrer tenure requirement: 120 days since opening your first checking account with us.
2. The referred enterprise must open a Beige Account
3. They must deposit at least $100,000 within 120 days

### Referral details
| Detail | Amount |
|---|---|
| Referrer bonus | $500 |
| Referred bonus | $350 |
| Maximum per year | 15 |
| Required deposit | $100,000 |
| Deposit window | 120 days |
| Minimum tenure | 120 days |

### How to participate
1. Contact your dedicated relationship manager for referral materials
2. Introduce qualified enterprises to the Beige Account benefits
3. Your relationship manager can facilitate introductions and track referrals
4. Bonuses are credited after all qualification requirements are confirmed

### Enterprise considerations
- Referrals must be for new Beige Account relationships
- Both enterprises must maintain accounts in good standing
- Premium referral bonuses reflect the enterprise-level relationship value

8. Business Silver Rewards Card: Referral Program - Earn Rewards for Referring Businesses
   ID: doc_business_credit_cards_business_silver_rewards_card_013
   Score: 14.7007
   Content: ## What you can earn
- Earn $100 for each successful referral that is approved and meets the qualifying spend requirement
- You can earn up to 10 referral bonuses per calendar year

## Qualifying spend requirement
- The referred business must spend at least $3,000 within 90 days of account opening for you to receive the bonus

## How to refer
- Share a referral through the official referral channel so applications are tracked correctly
- Ensure the referred business uses your referral details when applying

## Tracking and payout
- After the referred business is approved and completes the qualifying spend, your $100 bonus will be processed according to program rules
- If a referral does not appear, contact support with the referred business name and application date so it can be investigated

9. Sky Blue: Understanding Your Free Period
   ID: doc_business_checking_accounts_sky_blue_002
   Score: 14.3261
   Content: ## What Your Free Period Covers
- Monthly maintenance fees are waived for 6 months.
- Your account features continue to function normally during this time.

## When It Begins and Ends
- The free period starts when your account is opened and runs for 6 months.
- You can track remaining time in your billing or plan details screen.

## What Happens After
- When the free period ends, the monthly maintenance fee becomes $25.00.
- No action is required to continue service; billing updates automatically.

## Managing Your Timeline
- Review your billing settings to confirm the free period end date.
- Set internal reminders to prepare for the transition to $25.00.

## Referral Program During Free Period
Even during your free period, you can participate in the referral program once eligible:
- Qualifying deposit: Referred startups must deposit at least $10,000 to trigger the bonus
- Time window: The deposit must be made within 90 days of account opening
- Your eligibility: Referrers must meet the 45-day tenure threshold based on their banking history with Rho-Bank.

10. Navy Blue Business Checking: Complete Guide
   ID: doc_business_checking_accounts_navy_blue_001
   Score: 14.2738
   Content: ## Key Account Costs and Limits

- Monthly maintenance fee: $0.00
- Annual Percentage Yield (APY) on balances: 0.5%
- Daily digital transfer limit: $25,000

### What you can expect day to day
- No minimum balance requirement, so you can use the account flexibly.
- Unlimited digital transfers within the daily limit of $25,000.
- Optional overdraft settings are available if you want coverage on eligible transactions.
- E-statements are included at no additional cost.

### Practical tips for managing your account
- Use e-statements to keep records organized and accessible.
- Plan larger transfers with the daily limit of $25,000 in mind; schedule across days if needed.
- Keep an eye on your balance to maximize earnings at 0.5%.

### Quick reference
| Item | Amount |
| --- | --- |
| Monthly maintenance fee | $0.00 |
| APY | 0.5% |
| Daily digital transfer limit | $25,000 |

## Business Referral Program

Grow your network and earn rewards by referring other businesses to Navy Blue:

| Referral Detail | Value |
| --- | --- |
| Your referral bonus | $100 |
| New business welcome bonus | $75 |
| Maximum referrals per year | 10 |
| Required qualifying deposit | $5,000 |
| Deposit must be made within | 90 days |
| Your account age requirement | 60 days |

To qualify: The referred business must open a Navy Blue account and deposit at least $5,000 within 90 days of account opening. Referrer eligibility requires having been a Rho-Bank checking customer for 60 days or more.


[Timing: retrieval=2ms, reranking=0ms, total=2ms]

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "id": "skill-9",
  "role": "tool",
  "requestor": "assistant",
  "error": false,
  "turn_idx": 19,
  "timestamp": "2026-11-15T01:52:46.778483"
}
```


</details>

<a id="m020"></a>

### M020 · assistant

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "skill-10",
      "name": "get_current_time",
      "arguments": {},
      "requestor": "assistant"
    }
  ],
  "is_audio": false,
  "turn_idx": 20,
  "timestamp": "2026-11-15T01:52:56.059869",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 9.280799718006165,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m021"></a>

### M021 · tool

The current time is 2025-11-14 03:40:00 EST.

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "id": "skill-10",
  "role": "tool",
  "requestor": "assistant",
  "error": false,
  "turn_idx": 21,
  "timestamp": "2026-11-15T01:52:56.060476"
}
```


</details>

<a id="m022"></a>

### M022 · assistant

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "skill-11",
      "name": "KB_search",
      "arguments": {
        "query": "Cobalt Blue business checking account guide fees minimum balance"
      },
      "requestor": "assistant"
    }
  ],
  "is_audio": false,
  "turn_idx": 22,
  "timestamp": "2026-11-15T01:52:56.068196",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 0.0071511900023324415,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m023"></a>

### M023 · tool

1. Internal: Opening Business Checking Accounts
   ID: doc_bank_accounts_bank_accounts_(general)_003
   Score: 16.6958
   Content: ## Eligibility Requirements

To open a business checking account, ensure all of the following are true:
1. The customer is verified.
2. The customer has at least one existing personal checking account with status OPEN.
3. The customer does not exceed 6 business checking accounts.
4. The customer has no accounts with status CLOSED.
5. The customer's existing checking account has a balance of at least $500.

## Opening Procedure

1. Verify customer identity.
2. Check eligibility requirements listed above.
3. Confirm the customer's desired account_class selection.
   - Business checking account_class options include Navy Blue, Cobalt Blue, True Blue, etc.
4. Use open_bank_account_4821 to open the account.

2. True Blue Account: Fee Waivers and Balance Requirements
   ID: doc_business_checking_accounts_true_blue_002
   Score: 15.6101
   Content: ## Waiving your monthly maintenance fee
- You will be charged $75.00 each month unless you meet the waiver threshold.
- The monthly maintenance fee is waived when your balance is at least $50,000 during the statement period.

## Minimum balance requirement vs. fee waiver threshold
- Minimum balance requirement: $25,000 to maintain the account and access premium features.
- Fee waiver threshold: $50,000 to waive the $75.00 monthly maintenance fee.
- Falling below $25,000 may limit access to premium features until your balance is restored.

## Overdrafts and shortfalls
- If your balance goes negative, a per-occurrence overdraft fee of $25.00 may apply.

## How to avoid fees
- Maintain a balance of at least $50,000 to waive the monthly maintenance fee.
- Set internal processes to monitor balances against both $25,000 and $50,000.
- If a shortfall is anticipated, transfer funds promptly to avoid the $25.00 and preserve eligibility for the fee waiver.

## True Blue Referral Program

Refer other high-volume businesses to True Blue and earn significant rewards:

| Benefit | Amount |
| --- | --- |
| Referrer bonus | $350 per referral |
| New member bonus | $250 |
| Maximum referrals per year | 15 |
| Qualifying deposit | $50,000 |
| Deposit window | 120 days |
| Account age requirement | 90 days |

### Referral requirements
- The referred business must deposit $50,000 within 120 days of opening their True Blue account.
- Eligibility is based on how long you've been a Rho-Bank checking customer. The account age threshold is 90 days, calculated from when you opened your oldest checking account.
- Referral bonuses are paid after qualification is confirmed and are subject to the annual limit of 15.

3. Internal: Ordering a Debit Card for a Bank Account
   ID: doc_bank_accounts_bank_accounts_(general)_023
   Score: 15.0221
   Content: Procedure for if the customer inquires about ordering a debit card linked to a specific checking account. Debit cards can only be ordered for checking accounts (personal or business) - savings accounts are not eligible for debit cards.

Eligibility requirements:
1) Customer must be verified
2) The account must be a checking account (account_type must be 'checking')
3) Account status must be OPEN
4) Account must have been open for at least 3 business days (excluding weekends)
5) Customer cannot have more than 1 active debit cards per checking account
6) Account must have a minimum balance of $25 (to cover potential fees)
7) Customer must be at least 18 years old (verify using date_of_birth)
8) Customer cannot have a pending debit card order for the same account (check debit_cards table for PENDING status)
9) Customer's address on file must be a valid US domestic address (international shipping is not available)
 

Delivery Options:
- STANDARD: Free shipping, arrives in 7-10 business days
- EXPEDITED: $15 fee, arrives in 3-5 business days
- RUSH: $35 fee, arrives in 1-2 business days, fees may vary based on account tier. 

Card Design Options:
- CLASSIC: Standard Rho-Bank blue design (default, no fee)
- PREMIUM: Metallic silver finish ($10 one-time fee)
- CUSTOM: Customer-uploaded image ($25 one-time fee, subject to approval), fees may vary ased on account tier. 

Steps:
1) Verify customer identity
2) Confirm which checking account the debit card should be linked to. 
3) Check eligibility requirements for the specified account
4) Ask customer for preferred delivery option (STANDARD, EXPEDITED, or RUSH) and explain fees. 
5) Ask customer for preferred card design (CLASSIC, PREMIUM, or CUSTOM) and explain fees. 
6) Confirm the address that the customer would like to mail the card to. 
7) Use order_debit_card_5739 to order the card. 
8) Inform customer of expected delivery timeframe and any applicable fees

Important Notes:
- Expedited and rush delivery fees are automatically deducted from the linked checking account
- If the account has insufficient funds for delivery or design fees, the order will fail
- Customers can track their card shipment status using the Rho-Bank mobile app
- New cards are automatically activated upon first use with PIN entry
- The customer's existing debit card (if any) will remain active until the new card is activated.

4. How to transition a Light Green Account to Blue or Green Account (checking)
   ID: doc_checking_accounts_light_green_account_010
   Score: 13.6338
   Content: ## Determine if the change is automatic
- If Yes is True, your account will convert to an eligible adult checking option automatically at the appropriate time.

## If the change is not automatic
- If Yes is False, initiate a move to Blue or Green Account (checking) by submitting an upgrade request and selecting your preferred account type.

### Before you switch
- Compare features and fees of Blue and Green Account (checking) to choose the best fit.
- Confirm that any scheduled payments or deposits will continue without interruption after the transition.

5. Internal: Business Checking Account Promotion - November 2025
   ID: doc_bank_accounts_bank_accounts_(general)_013
   Score: 13.2183
   Content: PROMOTION NOTICE - ACTIVE FROM 11/01/2025 TO 11/30/2025: When recommending business checking accounts to customers, if multiple accounts meet all of the customer's stated requirements, agents should prioritize recommending accounts in the following order: (1) Sky Blue account should be recommended first, as it is currently under promotional priority; (2) Lime Green account should be recommended second, as it is also under promotional priority; (3) All other qualifying accounts may be recommended only if neither Sky Blue nor Lime Green meet the customer's requirements. This promotion is designed to increase adoption of our startup and premium business offerings. Always ensure the recommended account still meets ALL of the customer's stated requirements - do not recommend a promotional account if it does not satisfy the customer's needs.

6. FAQ: Blue Account
   ID: doc_checking_accounts_blue_account_010
   Score: 12.9871
   Content: ## Frequently asked questions

### What does a paper statement cost?
Paper statements are available for $2.50 per month.

### What APY do I earn on my balance?
Your Blue Account earns 0.01% APY on balances.

### Can I set low-balance alerts?
Yes. You can enable alerts at a threshold such as $62 so you are notified when your available balance reaches that level.

### How long do external bank transfers take?
Transfers to another bank typically complete in 2 business days.

### What happens if a deposited check is returned unpaid?
If a deposited check is returned by the issuing bank, a returned deposit fee of $15.00 applies.

### Is there a fee to receive a domestic wire?
Yes. Incoming domestic wires are assessed a fee of $12.50 per wire.

### Does the Blue Account have a referral program?
Yes. When you refer someone to open a Blue Account, you earn $35 for each successful referral. The person you refer receives $30 as a welcome bonus.

### What are the requirements for the referral bonus?
The referred person must deposit at least $500 within 60 days of opening their account. A minimum banking relationship of 30 days is required to participate—this is measured from when you first opened any checking account with us.

### Is there a limit to how many referral bonuses I can earn?
Yes. You can earn up to 5 referral bonuses per calendar year.

7. Getting Started with World Blue International Checking
   ID: doc_business_checking_accounts_world_blue_001
   Score: 12.5261
   Content: ## Quick checklist before you begin
- Confirm you can maintain at least $10,000 across currencies to keep the account in good standing
- Be aware of the monthly maintenance fee of $50.00
- Decide which of the up to 35 supported currencies you plan to hold and transact in
- Verify that your intended counterparties and destinations are within the $140 supported regions for sending and receiving payments

## Initial setup steps
- Fund your account so you can meet ongoing balance needs
- Add the currency wallets you will use for operations and settlements
- Set a primary operating currency for reporting and reconciliation
- Configure payee profiles for your frequent counterparties within the supported regions
- Review user access and prepare to assign permissions based on roles and responsibilities

## Key thresholds and limits at a glance

| Item | Value |
|---|---|
| Monthly maintenance fee | $50.00 |
| Minimum balance requirement | $10,000 |
| Supported currencies | 35 |
| Supported regions for payments | $140 |

## First-week best practices
- Keep an operating buffer above $10,000 to avoid service interruptions
- Start with a small set of currency wallets and expand as your payment flows stabilize
- Validate a test payment to a known counterparty in one of the supported regions and confirm posting and reconciliation
- Set alerts and reports aligned to your treasury cadence to monitor balances and activity

## Referring other businesses to World Blue

As a Rho-Bank checking account holder, you can refer other businesses to World Blue. To be eligible to refer:
- You must have maintained checking account status with Rho-Bank for at least 90 days

For a referral to qualify:
- The referred business must open a World Blue account
- They must deposit at least $25,000 within 90 days of account opening


8. Navy Blue Business Checking: Complete Guide
   ID: doc_business_checking_accounts_navy_blue_001
   Score: 11.8552
   Content: ## Key Account Costs and Limits

- Monthly maintenance fee: $0.00
- Annual Percentage Yield (APY) on balances: 0.5%
- Daily digital transfer limit: $25,000

### What you can expect day to day
- No minimum balance requirement, so you can use the account flexibly.
- Unlimited digital transfers within the daily limit of $25,000.
- Optional overdraft settings are available if you want coverage on eligible transactions.
- E-statements are included at no additional cost.

### Practical tips for managing your account
- Use e-statements to keep records organized and accessible.
- Plan larger transfers with the daily limit of $25,000 in mind; schedule across days if needed.
- Keep an eye on your balance to maximize earnings at 0.5%.

### Quick reference
| Item | Amount |
| --- | --- |
| Monthly maintenance fee | $0.00 |
| APY | 0.5% |
| Daily digital transfer limit | $25,000 |

## Business Referral Program

Grow your network and earn rewards by referring other businesses to Navy Blue:

| Referral Detail | Value |
| --- | --- |
| Your referral bonus | $100 |
| New business welcome bonus | $75 |
| Maximum referrals per year | 10 |
| Required qualifying deposit | $5,000 |
| Deposit must be made within | 90 days |
| Your account age requirement | 60 days |

To qualify: The referred business must open a Navy Blue account and deposit at least $5,000 within 90 days of account opening. Referrer eligibility requires having been a Rho-Bank checking customer for 60 days or more.

9. Troubleshooting: Unexpected Charges on Cobalt Blue
   ID: doc_business_checking_accounts_cobalt_blue_009
   Score: 11.8293
   Content: ## Identify the charge
- Review the exact transaction description on your statement or in your transaction history (e.g., “Monthly Maintenance Fee,” “Wire Transfer – Domestic,” “ATM Fee,” “International ATM Withdrawal Fee,” “Excess Transaction Fee”).
- Note the posting date, amount, and any memo or terminal/location details.
- Compare the posting date to your recent account activity (wires sent, ATM withdrawals, transaction volume, month-end).

## Common Cobalt Blue charges that may appear
| Line item on statement | Why it appears | How to confirm | Amount |
|---|---|---|---|
| Monthly Maintenance Fee | Your account did not meet the balance waiver requirement during the statement period. | Check the Fee Summary on your statement and verify whether your balance met $2,500 for the period. | $20.00 |
| Excess Transaction Fee | You exceeded your monthly free transaction limit. | Count your posted transactions for the statement period and compare to your free allowance; the fee line often notes the number of excess items. | $0.25 per excess transaction |
| Wire Transfer Fee – Domestic | You initiated a domestic wire transfer. | Confirm a wire was submitted on or near the posting date in your transfer history. | $20.00 |
| ATM Fee – Out of Network | You used a non‑Rho ATM in the U.S. | Match the fee date to an ATM withdrawal at a non‑Rho terminal. Note: the ATM owner may also assess a separate surcharge. | $2.00 per ATM transaction |
| International ATM Withdrawal Fee | You withdrew cash at a foreign (international) ATM. | Match the fee date/location to an overseas ATM withdrawal. | 2.5% of the withdrawal amount, minimum $4.00 |

Note: Cobalt Blue does not assess overdraft fees. If you see a charge that appears to be an overdraft fee, review the line’s exact description—it may correspond to one of the fees above. If still unclear, request a review.

## Troubleshooting by charge type

### Monthly Maintenance Fee posted unexpectedly
- Verify whether your account met the waiver balance requirement of $2,500 during the statement period.
- Check if the fee posted at or just after the statement cycle date.
- Compare your balance history for the full period; large debits near period‑end can affect waiver eligibility.
- If you believe you qualified for the waiver, request a fee review and include your statement period dates and balance evidence.

### Excess Transaction Fee you didn’t anticipate
- Add up your posted transactions for the statement period and compare to your plan’s free monthly transaction limit.
- Open the fee detail to see how many items were assessed at $0.25 each.
- If the count appears off, provide a list of the transactions you believe were miscounted when requesting a review.

### Wire Transfer Fee – Domestic you didn’t expect
- Confirm whether a domestic wire was sent on the fee date (or one business day prior).
- Distinguish wires from other transfers by the transaction description (“Wire,” routing via Fedwire, etc.).
- If you did not authorize a wire, report immediately for investigation. Otherwise, the standard fee is $20.00.

### ATM fees: domestic vs. international
- Out‑of‑network (domestic) ATM usage: Expect $2.00 per ATM transaction. This is separate from any surcharge by the ATM owner, which can appear as a separate line item.
- Foreign (international) ATM withdrawals: The fee is 2.5% of the withdrawal amount, with a minimum of $4.00. Example: for a withdrawal, multiply the amount by 2.5%; if that result is less than $4.00, the minimum applies.

## Quick checklist before requesting a review
- Match the fee’s posting date to a specific action (wire, ATM withdrawal, month‑end, spike in transaction volume).
- Capture screenshots of:
  - The fee line item (showing date, amount, and description)
  - Any related transaction (wire confirmation, ATM withdrawal)
  - The relevant statement page (Fee Summary and balance history for the period)
- Briefly explain why the fee appears incorrect (e.g., you met $2,500 during the period, transaction count appears miscalculated, withdrawal was domestic vs. international, etc.).

## Requesting a review or dispute
- Contact us as soon as you notice the charge.
- Include: account name, last 4 digits, statement period, fee date/amount/description, and your supporting screenshots or documents.
- We will investigate and correct any misapplied fees. If additional information is needed (e.g., to verify ATM location or wire authorization), we will follow up.

10. Linked Checking Account APY Boosts for Savings Accounts
   ID: doc_bank_accounts_bank_accounts_(general)_012
   Score: 11.5089
   Content: Certain personal checking and savings account pairings provide bonus APY on your savings account balance. When you hold both a qualifying checking account and savings account under the same customer profile, the APY boost is automatically applied to your savings account. The following checking and savings account pairings qualify for APY boosts:

1. Green Account (checking) + Gold Account (savings)
2. Green Fee-Free Account (checking) + Bronze Account (savings)
3. Evergreen Account (checking) + Green Account (savings)
4. Blue Account (checking) + Silver Plus Account (savings)
5. Light Green Account (checking) + Diamond Elite Account (savings)
6. Dark Green Account (checking) + Bronze Account (savings)
7. Bluest Account (checking) + Silver Account (savings)
8. Purple Account (checking) + Platinum Plus Account (savings)
9. Gold Years Account (checking) + Gold Plus Account (savings)
10. Light Green Account (checking) + Platinum Account (savings)
11. Green Account (checking) + Silver Account (savings)
12. Evergreen Account (checking) + Diamond Elite Account (savings)
13. Bluest Account (checking) + Bronze Account (savings)
14. Purple Account (checking) + Gold Account (savings)
15. Gold Years Account (checking) + Silver Account (savings)
16. Blue Account (checking) + Platinum Account (savings)
17. Green Fee-Free Account (checking) + Gold Plus Account (savings)
18. Dark Green Account (checking) + Platinum Plus Account (savings)

Note: Only these specific pairings qualify for the linked checking account APY boost. All other checking and savings account combinations do not receive any APY boost from linking. The boost is additive to your savings account's base APY and any credit card APY bonuses you may already have. For the exact APY boost percentages for each pairing, please refer to the specific savings account documentation.


[Timing: retrieval=2ms, reranking=0ms, total=2ms]

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "id": "skill-11",
  "role": "tool",
  "requestor": "assistant",
  "error": false,
  "turn_idx": 23,
  "timestamp": "2026-11-15T01:52:56.071182"
}
```


</details>

<a id="m024"></a>

### M024 · assistant

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "skill-12",
      "name": "KB_search",
      "arguments": {
        "query": "World Blue business checking account eligibility international"
      },
      "requestor": "assistant"
    }
  ],
  "is_audio": false,
  "turn_idx": 24,
  "timestamp": "2026-11-15T01:52:56.081737",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 0.009583820996340364,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m025"></a>

### M025 · tool

1. Getting Started with World Blue International Checking
   ID: doc_business_checking_accounts_world_blue_001
   Score: 17.6320
   Content: ## Quick checklist before you begin
- Confirm you can maintain at least $10,000 across currencies to keep the account in good standing
- Be aware of the monthly maintenance fee of $50.00
- Decide which of the up to 35 supported currencies you plan to hold and transact in
- Verify that your intended counterparties and destinations are within the $140 supported regions for sending and receiving payments

## Initial setup steps
- Fund your account so you can meet ongoing balance needs
- Add the currency wallets you will use for operations and settlements
- Set a primary operating currency for reporting and reconciliation
- Configure payee profiles for your frequent counterparties within the supported regions
- Review user access and prepare to assign permissions based on roles and responsibilities

## Key thresholds and limits at a glance

| Item | Value |
|---|---|
| Monthly maintenance fee | $50.00 |
| Minimum balance requirement | $10,000 |
| Supported currencies | 35 |
| Supported regions for payments | $140 |

## First-week best practices
- Keep an operating buffer above $10,000 to avoid service interruptions
- Start with a small set of currency wallets and expand as your payment flows stabilize
- Validate a test payment to a known counterparty in one of the supported regions and confirm posting and reconciliation
- Set alerts and reports aligned to your treasury cadence to monitor balances and activity

## Referring other businesses to World Blue

As a Rho-Bank checking account holder, you can refer other businesses to World Blue. To be eligible to refer:
- You must have maintained checking account status with Rho-Bank for at least 90 days

For a referral to qualify:
- The referred business must open a World Blue account
- They must deposit at least $25,000 within 90 days of account opening


2. Earning Interest on Your World Blue Balance
   ID: doc_business_checking_accounts_world_blue_007
   Score: 17.0785
   Content: ## Rate and compounding
- Your USD balance earns an Annual Percentage Yield of 1.0%
- Interest is compounded daily

## How interest is applied
- Interest accrues on eligible USD funds held in the account and is credited in accordance with your statement cycle
- If you move funds between currencies, only USD balances accrue interest at 1.0%

## Monitoring your earnings
- Track accrued and credited interest in your account activity and statements
- Export transaction data to reconcile interest income in your general ledger

## Tips for maximizing earned interest
- Keep operational reserves in USD when appropriate so they benefit from compounding daily
- Align conversion and payout timing with your cash needs so idle USD balances remain interest-earning as long as practicable

## Referral bonuses for World Blue members

In addition to interest earnings, you can earn rewards by referring other international businesses to World Blue:

- **Your bonus**: $300 for each successful referral
- **Their bonus**: $200 welcome bonus for the new business
- **Annual limit**: 12 referral bonuses per calendar year

Referral bonuses are typically credited within 7-10 business days of qualification. Both accounts must remain in good standing for bonuses to be paid.


3. Internal: Business Checking Account Promotion - November 2025
   ID: doc_bank_accounts_bank_accounts_(general)_013
   Score: 13.2183
   Content: PROMOTION NOTICE - ACTIVE FROM 11/01/2025 TO 11/30/2025: When recommending business checking accounts to customers, if multiple accounts meet all of the customer's stated requirements, agents should prioritize recommending accounts in the following order: (1) Sky Blue account should be recommended first, as it is currently under promotional priority; (2) Lime Green account should be recommended second, as it is also under promotional priority; (3) All other qualifying accounts may be recommended only if neither Sky Blue nor Lime Green meet the customer's requirements. This promotion is designed to increase adoption of our startup and premium business offerings. Always ensure the recommended account still meets ALL of the customer's stated requirements - do not recommend a promotional account if it does not satisfy the customer's needs.

4. True Blue Account: Fee Waivers and Balance Requirements
   ID: doc_business_checking_accounts_true_blue_002
   Score: 13.1407
   Content: ## Waiving your monthly maintenance fee
- You will be charged $75.00 each month unless you meet the waiver threshold.
- The monthly maintenance fee is waived when your balance is at least $50,000 during the statement period.

## Minimum balance requirement vs. fee waiver threshold
- Minimum balance requirement: $25,000 to maintain the account and access premium features.
- Fee waiver threshold: $50,000 to waive the $75.00 monthly maintenance fee.
- Falling below $25,000 may limit access to premium features until your balance is restored.

## Overdrafts and shortfalls
- If your balance goes negative, a per-occurrence overdraft fee of $25.00 may apply.

## How to avoid fees
- Maintain a balance of at least $50,000 to waive the monthly maintenance fee.
- Set internal processes to monitor balances against both $25,000 and $50,000.
- If a shortfall is anticipated, transfer funds promptly to avoid the $25.00 and preserve eligibility for the fee waiver.

## True Blue Referral Program

Refer other high-volume businesses to True Blue and earn significant rewards:

| Benefit | Amount |
| --- | --- |
| Referrer bonus | $350 per referral |
| New member bonus | $250 |
| Maximum referrals per year | 15 |
| Qualifying deposit | $50,000 |
| Deposit window | 120 days |
| Account age requirement | 90 days |

### Referral requirements
- The referred business must deposit $50,000 within 120 days of opening their True Blue account.
- Eligibility is based on how long you've been a Rho-Bank checking customer. The account age threshold is 90 days, calculated from when you opened your oldest checking account.
- Referral bonuses are paid after qualification is confirmed and are subject to the annual limit of 15.

5. FAQ: Checking Account Referrals
   ID: doc_bank_accounts_bank_accounts_(general)_048
   Score: 13.0657
   Content: ## Frequently asked questions about checking account referrals

### How many people can I refer at once?
You can have multiple referrals in progress, but you can only receive a maximum of 2 referral bonuses in any rolling 9-day window. If you exceed this limit, additional referrals will be automatically denied until enough time passes.

### Can I refer someone who used to have a Rho-Bank account?
No. The referred person must be a new Rho-Bank customer with no existing or closed accounts within the past 12 months. Former customers must wait 12 months after their last account closure before being eligible as a referral.

### Can I refer someone who lives at the same address as me?
No. The referrer and referred person cannot be registered at the same address. This restriction helps prevent abuse of the referral program.

### What counts as a qualifying deposit?
The qualifying deposit must be new money brought into Rho-Bank. Transfers from another Rho-Bank account do not count. The deposit can come from an external bank transfer, direct deposit, mobile check deposit, or cash/check deposit at a branch.

### What happens if the person I referred closes their account early?
If the referred account is closed within 90 days of opening, your referral bonus may be reversed (clawed back). Both accounts must remain in good standing for bonuses to be retained.

### Can I combine the referral bonus with other promotions?
No. The referral bonus cannot be combined with other new account promotions or sign-up bonuses. Only one promotional offer can be applied per new account.

### What do the referral statuses mean?
- **COMPLETE**: The referral was successful and bonuses will be paid.
- **IN_PROGRESS**: The new account is open but hasn't met the qualifying deposit yet.
- **NO_PROGRESS**: The referred person hasn't started an application.
- **APPLIED**: An application has been submitted and is being reviewed.
- **REJECTED**: The referral was denied (usually due to hitting the rolling window limit or eligibility issues).
- **ERROR**: A system error occurred; try again later or contact support.

### Why was my referral rejected?
Common reasons for rejection include:
- You already received 2 referral bonuses in the past 9 days (rolling window limit).
- The referred person already has or recently had a Rho-Bank account.
- You and the referred person are registered at the same address.
- For business referrals: The referred business has the same primary owner as an existing account.

### How long do I have to wait after a rejection to refer again?
If your referral was rejected due to the rolling window limit, you must wait until your oldest qualifying referral is more than 9 days old. The limit is based on a rolling window, so you become eligible again as older referrals age out.

### Can I refer someone for a business checking account?
Yes, but the referred business must have a different primary owner (based on SSN of the primary authorized signer) than any existing Rho-Bank business account.

### Do I need to have the same account type to refer someone for it?
No. Referrer eligibility hinges on how long you've been a Rho-Bank checking customer, not which product you currently use. The tenure threshold is measured from when you opened your very first checking account with us. Someone with a Navy Blue account can refer others for World Blue, True Blue, or any other checking product—provided they've met the duration requirement.

### How long does the referred person have to make the qualifying deposit?
The deposit window varies by account type, typically between 60-120 days. Check the specific account's referral terms for the exact timeframe. After the deposit is made, it must remain in the account for at least 30 additional days.

6. Internal: Ordering a Debit Card for a Bank Account
   ID: doc_bank_accounts_bank_accounts_(general)_023
   Score: 12.9930
   Content: Procedure for if the customer inquires about ordering a debit card linked to a specific checking account. Debit cards can only be ordered for checking accounts (personal or business) - savings accounts are not eligible for debit cards.

Eligibility requirements:
1) Customer must be verified
2) The account must be a checking account (account_type must be 'checking')
3) Account status must be OPEN
4) Account must have been open for at least 3 business days (excluding weekends)
5) Customer cannot have more than 1 active debit cards per checking account
6) Account must have a minimum balance of $25 (to cover potential fees)
7) Customer must be at least 18 years old (verify using date_of_birth)
8) Customer cannot have a pending debit card order for the same account (check debit_cards table for PENDING status)
9) Customer's address on file must be a valid US domestic address (international shipping is not available)
 

Delivery Options:
- STANDARD: Free shipping, arrives in 7-10 business days
- EXPEDITED: $15 fee, arrives in 3-5 business days
- RUSH: $35 fee, arrives in 1-2 business days, fees may vary based on account tier. 

Card Design Options:
- CLASSIC: Standard Rho-Bank blue design (default, no fee)
- PREMIUM: Metallic silver finish ($10 one-time fee)
- CUSTOM: Customer-uploaded image ($25 one-time fee, subject to approval), fees may vary ased on account tier. 

Steps:
1) Verify customer identity
2) Confirm which checking account the debit card should be linked to. 
3) Check eligibility requirements for the specified account
4) Ask customer for preferred delivery option (STANDARD, EXPEDITED, or RUSH) and explain fees. 
5) Ask customer for preferred card design (CLASSIC, PREMIUM, or CUSTOM) and explain fees. 
6) Confirm the address that the customer would like to mail the card to. 
7) Use order_debit_card_5739 to order the card. 
8) Inform customer of expected delivery timeframe and any applicable fees

Important Notes:
- Expedited and rush delivery fees are automatically deducted from the linked checking account
- If the account has insufficient funds for delivery or design fees, the order will fail
- Customers can track their card shipment status using the Rho-Bank mobile app
- New cards are automatically activated upon first use with PIN entry
- The customer's existing debit card (if any) will remain active until the new card is activated.

7. Light Blue Account Referral Program
   ID: doc_checking_accounts_light_blue_account_007
   Score: 12.2856
   Content: ## Earn rewards by referring friends

Share the Light Blue Account with others and earn cash bonuses.

### What you earn
- Referral bonus: $30 for each successful referral
- Maximum referrals: 5 per calendar year

### What they receive
- Welcome bonus: $20 when they open and fund their account

### Requirements

| Requirement | Detail |
|---|---|
| Qualifying deposit | $500 |
| Deposit window | Within 60 days of account opening |
| Referrer tenure | 30 days |

### How it works
1. Share your unique referral link with friends and family
2. They open a Light Blue Account using your link
3. They deposit at least $500 within 60 days
4. You receive $30 and they receive $20

### Eligibility
- To qualify as a referrer, you must have been a Rho-Bank checking account holder for 30 days or longer.
- You can earn up to 5 referral bonuses per calendar year

8. Internal: Opening Business Checking Accounts
   ID: doc_bank_accounts_bank_accounts_(general)_003
   Score: 12.2526
   Content: ## Eligibility Requirements

To open a business checking account, ensure all of the following are true:
1. The customer is verified.
2. The customer has at least one existing personal checking account with status OPEN.
3. The customer does not exceed 6 business checking accounts.
4. The customer has no accounts with status CLOSED.
5. The customer's existing checking account has a balance of at least $500.

## Opening Procedure

1. Verify customer identity.
2. Check eligibility requirements listed above.
3. Confirm the customer's desired account_class selection.
   - Business checking account_class options include Navy Blue, Cobalt Blue, True Blue, etc.
4. Use open_bank_account_4821 to open the account.

9. Internal: Opening Business Savings Accounts
   ID: doc_bank_accounts_bank_accounts_(general)_004
   Score: 11.8111
   Content: ## Description

Procedure for opening business savings accounts. Eligibility requirements: 1) Customer must be verified, 2) Customer must already have at least one business checking account with status OPEN, 3) Customer cannot have more than 4 business savings accounts, 4) Customer must not have any accounts with negative balances, 5) Existing business checking account must have been open for at least 30 days, 6) Existing business checking account must have a balance of at least $2,500. Steps: 1) Verify customer identity, 2) Check eligibility requirements, 3) Confirm account selection with customer (business savings account_class options include Bronze Saver Account, Silver Saver Account, etc.), 4) Use open_bank_account_4821 to open the account, 5) Ask the customer if they would like you to transfer the opening deposit from their business checking account now. If yes, use transfer_funds_between_bank_accounts_7291 to transfer the required amount. If no, inform them they have 30 days to fund the account (via internal transfer or external deposit) or the account will be closed.

## Eligibility Requirements

Confirm all of the following before proceeding:
- Customer identity is verified.
- Customer has at least one business checking account with status OPEN.
- Customer has fewer than 4 existing business savings accounts.
- Customer has no accounts with negative balances.
- At least one existing business checking account has been open for at least 30 days.
- That business checking account has a current balance of at least $2,500.

Notes:
- Use the qualifying OPEN business checking account that meets both the tenure and balance thresholds as the source for the optional opening deposit transfer.

## Step-by-Step Procedure

1) Verify customer identity.
2) Check eligibility requirements (see list above).
3) Confirm account selection with the customer:
   - Ask for the desired business savings account_class (e.g., Bronze Saver Account, Silver Saver Account, etc.).
   - Ensure you capture the exact official account_class name ending with “Account.”
4) Open the new business savings account using the agent tool (see Tool Instructions below).
5) Funding the opening deposit:
   - Ask the customer if they want you to transfer the opening deposit now from their eligible business checking account.
   - If yes: initiate the internal transfer using the agent tool (see Tool Instructions below).
   - If no: inform the customer they have 30 days to fund the account via internal transfer or external deposit; otherwise, the account will be closed.

## Agent Tool Instructions

The AGENT calls these tools directly to perform actions on behalf of the customer. Do not expose tool details to the customer.

### Tool: open_bank_account_4821

- Signature:
  - open_bank_account_4821(user_id, account_type, account_class)
- When to call:
  - After eligibility is confirmed and the customer has selected the desired business savings account_class.
- How to call:
  - Set account_type to 'savings'.
  - Set account_class to the exact official name provided by the customer (e.g., 'Bronze Saver Account').
- Expected outcome:
  - Returns a new savings account record (capture the new account_id for subsequent actions).

### Tool: transfer_funds_between_bank_accounts_7291

- Signature:
  - transfer_funds_between_bank_accounts_7291(source_account_id, destination_account_id, amount)
- When to call:
  - Only if the customer authorizes transferring the opening deposit now.
- How to call:
  - source_account_id: the qualifying OPEN business checking account that meets the 30-day tenure and $2,500 balance requirements.
  - destination_account_id: the newly opened business savings account_id.
  - amount: the required opening deposit amount confirmed with the customer.
- If the transfer fails (e.g., insufficient funds):
  - Inform the customer and remind them they have 30 days to fund the account via internal transfer or external deposit, or the account will be closed.

## Checklist Before Opening

- Customer identity verified.
- OPEN business checking account identified and qualified (≥ 30 days open and ≥ $2,500 balance).
- Savings account count confirmed is < 4.
- No negative balances across any accounts.
- Customer-confirmed account_class captured exactly.

## Post-Opening Actions

- If the customer funds now: complete the transfer and confirm success.
- If the customer defers funding: clearly communicate the 30-day deadline and acceptable methods (internal transfer or external deposit), and note that the account will be closed if not funded within that timeframe.

10. How to transition a Light Green Account to Blue or Green Account (checking)
   ID: doc_checking_accounts_light_green_account_010
   Score: 11.6335
   Content: ## Determine if the change is automatic
- If Yes is True, your account will convert to an eligible adult checking option automatically at the appropriate time.

## If the change is not automatic
- If Yes is False, initiate a move to Blue or Green Account (checking) by submitting an upgrade request and selecting your preferred account type.

### Before you switch
- Compare features and fees of Blue and Green Account (checking) to choose the best fit.
- Confirm that any scheduled payments or deposits will continue without interruption after the transition.


[Timing: retrieval=2ms, reranking=0ms, total=2ms]

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "id": "skill-12",
  "role": "tool",
  "requestor": "assistant",
  "error": false,
  "turn_idx": 25,
  "timestamp": "2026-11-15T01:52:56.085354"
}
```


</details>

<a id="m026"></a>

### M026 · assistant

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "skill-13",
      "name": "KB_search",
      "arguments": {
        "query": "business checking account list Silver Gold Platinum Purple"
      },
      "requestor": "assistant"
    }
  ],
  "is_audio": false,
  "turn_idx": 26,
  "timestamp": "2026-11-15T01:53:09.287874",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 13.20146884699352,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m027"></a>

### M027 · tool

1. Linked Checking Account APY Boosts for Savings Accounts
   ID: doc_bank_accounts_bank_accounts_(general)_012
   Score: 27.0625
   Content: Certain personal checking and savings account pairings provide bonus APY on your savings account balance. When you hold both a qualifying checking account and savings account under the same customer profile, the APY boost is automatically applied to your savings account. The following checking and savings account pairings qualify for APY boosts:

1. Green Account (checking) + Gold Account (savings)
2. Green Fee-Free Account (checking) + Bronze Account (savings)
3. Evergreen Account (checking) + Green Account (savings)
4. Blue Account (checking) + Silver Plus Account (savings)
5. Light Green Account (checking) + Diamond Elite Account (savings)
6. Dark Green Account (checking) + Bronze Account (savings)
7. Bluest Account (checking) + Silver Account (savings)
8. Purple Account (checking) + Platinum Plus Account (savings)
9. Gold Years Account (checking) + Gold Plus Account (savings)
10. Light Green Account (checking) + Platinum Account (savings)
11. Green Account (checking) + Silver Account (savings)
12. Evergreen Account (checking) + Diamond Elite Account (savings)
13. Bluest Account (checking) + Bronze Account (savings)
14. Purple Account (checking) + Gold Account (savings)
15. Gold Years Account (checking) + Silver Account (savings)
16. Blue Account (checking) + Platinum Account (savings)
17. Green Fee-Free Account (checking) + Gold Plus Account (savings)
18. Dark Green Account (checking) + Platinum Plus Account (savings)

Note: Only these specific pairings qualify for the linked checking account APY boost. All other checking and savings account combinations do not receive any APY boost from linking. The boost is additive to your savings account's base APY and any credit card APY bonuses you may already have. For the exact APY boost percentages for each pairing, please refer to the specific savings account documentation.

2. Internal: Credit Card Rewards - Points vs Cash Back Representation
   ID: doc_credit_cards_credit_cards_(general)_006
   Score: 19.4605
   Content: ## Rewards representation
Due to a legacy backend migration that has not yet been completed, all credit card rewards in the transaction database are stored as 'points' regardless of whether the card is a cash back card or a points-based card. For cash back cards (Bronze Rewards Card, Silver Rewards Card, Gold Rewards Card, Platinum Rewards Card, Diamond Elite Card, Crypto-Cash Back, Business Bronze Rewards Card, Business Silver Rewards Card, Green Rewards Card, Silver Zoom Card, Business Gold Rewards Card, and Business Platinum Rewards Card), these 'points' should be interpreted as cash back with a conversion rate of 1 point = $0.01 when redeemed as a statement credit or as a credit to the user's Rho-Bank checking account. For example, 250 points equals $2.50 in cash back, which matches a 2.5% cash back rate on a $100 purchase. The only true points-based card is the EcoCard, which earns 'sustainability points' (5 points per dollar on green purchases, 1 point per dollar on other purchases) that also redeem at $0.01 per point when redeemed as a statement credit or checking account credit.

3. Gold Saver Account: Business Credit Card APY Bonuses
   ID: doc_business_savings_accounts_gold_saver_account_009
   Score: 19.1364
   Content: ## APY bonus amounts by eligible business card
The following APY bonuses are available on your Gold Saver Account when you hold an eligible Rho Business Rewards Card. Each bonus is added as percentage points to your existing Gold Saver Account APY.

- Business Silver Rewards Card: 0.2% percentage points
- Business Gold Rewards Card: 0.4% percentage points
- Business Platinum Rewards Card: 0.6% percentage points

### Summary table
| Eligible card | APY bonus (percentage points) |
| --- | --- |
| Business Silver Rewards Card | 0.2% |
| Business Gold Rewards Card | 0.4% |
| Business Platinum Rewards Card | 0.6% |

## How the APY bonus is applied
- The applicable APY bonus is added to the APY associated with your current Gold Saver Account balance tier.
- The adjusted APY (base APY plus any applicable bonus) is used to calculate interest accrued on your Gold Saver Account.
- If your card eligibility changes, your Gold Saver Account APY will be updated after the change is processed and reflected in your account details.

## Example calculations
- If your base Gold Saver APY is X%, and you hold a Business Silver Rewards Card, your effective APY becomes X% + 0.2%.
- If your base Gold Saver APY is X%, and you hold a Business Gold Rewards Card, your effective APY becomes X% + 0.4%.
- If your base Gold Saver APY is X%, and you hold a Business Platinum Rewards Card, your effective APY becomes X% + 0.6%.

## How to confirm your APY bonus
1. Sign in to your Rho account.
2. Open your Gold Saver Account details.
3. Check the APY displayed; if you are eligible, it will include the applicable APY bonus shown above.

4. Silver Plus Saver Account: Complete Guide
   ID: doc_business_savings_accounts_silver_plus_saver_001
   Score: 16.5784
   Content: ## Eligibility and Minimum Balance
- You must maintain a minimum balance of $5,000 to keep the Silver Plus Saver account in good standing.
- If your balance is anticipated to dip below $5,000, consider timing deposits and withdrawals to avoid falling under the requirement.

## Interest and APY Structure
- Balances below the tier 2 threshold earn 2.5% APY.
- Balances above the tier 2 threshold earn 4.0% APY.

### Relationship APY Bonuses
If you hold an eligible Business Rewards Card, an APY bonus is added to your base APY:
- Business Silver Rewards Card: +0.18% APY
- Business Gold Rewards Card: +0.38% APY
- Business Platinum Rewards Card: +0.62% APY

The bonus applies to the base APY for the balance tier you qualify for.

### Example APYs With Relationship Bonuses
Below are example total APYs when a relationship bonus applies:

- Balance below tier 2 threshold (base 2.5%):
  - With Business Silver Rewards Card: 2.68% (2.5% + 0.18%)
  - With Business Gold Rewards Card: 2.88% (2.5% + 0.38%)
  - With Business Platinum Rewards Card: 3.12% (2.5% + 0.62%)

- Balance above tier 2 threshold (base 4.0%):
  - With Business Silver Rewards Card: 4.18% (4.0% + 0.18%)
  - With Business Gold Rewards Card: 4.38% (4.0% + 0.38%)
  - With Business Platinum Rewards Card: 4.62% (4.0% + 0.62%)

## Withdrawals and Transfers
Silver Plus Saver offers higher withdrawal limits and improved transfer capabilities compared to Silver Saver. To make the most of these enhancements:
- Plan large withdrawals in advance to ensure smooth processing.
- Use scheduled transfers for recurring payments to maintain your target balance above $5,000.
- For unusually large or time-sensitive transfers, initiate earlier in the business day to reduce the risk of delays.

## Upgrading from Silver Saver
If you are moving up from Silver Saver:
- Confirm you can maintain at least $5,000 in Silver Plus Saver.
- Request an upgrade through your online banking or by contacting support. Your balances will begin earning at the Silver Plus Saver rates as soon as the upgrade is completed.

## How to Verify Your Current APY and Bonus
- In online banking, open the Silver Plus Saver account details to view:
  - Your current balance tier (below or above the tier 2 threshold)
  - Base APY for that tier (2.5% or 4.0%)
  - Any relationship APY bonus applied (e.g., 0.38%) 
- Review after any balance change or card status update to confirm your effective APY.

5. Diamond Vault Account: Business Credit Card APY Bonuses
   ID: doc_business_savings_accounts_diamond_vault_008
   Score: 16.3996
   Content: ## Available APY Bonuses by Card Tier

The following Business Rewards Cards increase your Diamond Vault APY by the indicated percentage points:

| Eligible Business Rewards Card | APY bonus (percentage points) |
| --- | --- |
| Business Silver Rewards Card | 0.3% |
| Business Gold Rewards Card | 0.55% |
| Business Platinum Rewards Card | 0.9% |

## How the APY bonus applies

- The bonus is additive: it is added to your Diamond Vault APY (it is not a multiplier).
- The applicable bonus is determined by the highest eligible Business Rewards Card your business holds.
- The bonus increases the APY used to calculate interest on your Diamond Vault account while you continue to hold the qualifying card.
- If you change card tier (e.g., upgrade or downgrade), the APY bonus adjusts to the new card’s bonus once the change is reflected on your account.
- Only one card-linked APY bonus applies to a Diamond Vault account at a time.

### Bonus amounts by tier
- Business Silver Rewards Card: +0.3%
- Business Gold Rewards Card: +0.55%
- Business Platinum Rewards Card: +0.9%

## Calculating your effective APY

- Formula: Effective APY = Diamond Vault APY + applicable card bonus
- Examples:
  - With a Business Silver Rewards Card: Effective APY = Diamond Vault APY + 0.3%
  - With a Business Gold Rewards Card: Effective APY = Diamond Vault APY + 0.55%
  - With a Business Platinum Rewards Card: Effective APY = Diamond Vault APY + 0.9%

## Activating or updating your bonus

- Ensure your Business Rewards Card is associated with the same business profile as your Diamond Vault account.
- If you obtain, upgrade, or replace a Business Rewards Card, the APY bonus will update to the corresponding tier once the new card is associated with your business profile.
- To verify your active bonus, review your Diamond Vault account details. If the displayed bonus does not match your card tier, contact support for assistance.

6. Platinum Reserve Account: Business Credit Card APY Bonuses
   ID: doc_business_savings_accounts_platinum_reserve_account_010
   Score: 14.9041
   Content: ## Eligible Business Credit Cards and APY Bonuses

Holding an eligible Rho-Bank Business Rewards Card can increase the APY on your Platinum Reserve Account. The increase is additive to your current APY and is reflected in your displayed rate and daily interest accruals.

- Business Silver Rewards Card: adds 0.25% to your APY
- Business Gold Rewards Card: adds 0.5% to your APY
- Business Platinum Rewards Card: adds 0.8% to your APY

## How the APY Bonus Is Applied

- The bonus is added as a fixed number of percentage points to your Platinum Reserve Account’s APY based on your eligible card tier.
- The bonus is included in your total APY and affects interest that accrues daily and credits on your normal interest crediting schedule.
- The bonus applies only for the period during which you are eligible; if eligibility begins or ends mid-cycle, the APY used for daily accruals adjusts as of the effective date of that change.

## Verifying Your Bonus

- Check the APY shown in your Platinum Reserve Account details; the increase from your eligible card will be included in the displayed APY.
- Your interest activity will reflect the higher daily accrual associated with the bonus.
- If you hold more than one eligible card or have recently changed cards, contact your Rho-Bank representative to confirm which bonus is currently applied.

## Maintaining Eligibility

To keep the APY bonus active:
- Ensure the eligible Business Rewards Card remains active and in good standing.
- Keep the card associated with the same business entity that owns the Platinum Reserve Account.
- Notify Rho-Bank promptly if your business ownership structure or card status changes, so your APY can be updated accordingly.

## Starting, Changing, or Removing a Bonus

- New or upgraded card: Once eligibility is confirmed, your APY will reflect the applicable bonus going forward.
- Card downgrade, closure, or ineligibility: The APY bonus will no longer apply from the effective date of the change.
- Multiple cards: If your organization holds multiple eligible cards, your account will reflect the applicable bonus for your configuration; contact your Rho-Bank representative if you need confirmation.

## Example (for illustration only)

- If your Platinum Reserve Account APY is 3.00% and you hold a Business Platinum Rewards Card, your APY would increase by 0.8% to 3.80%.
- If your APY is 2.75% and you hold a Business Gold Rewards Card, your APY would increase by 0.5% to 3.25%.
- If your APY is 2.25% and you hold a Business Silver Rewards Card, your APY would increase by 0.25% to 2.50%.

7. Credit Card Replacement Shipping Options and Fees
   ID: doc_credit_cards_credit_card_replacements_002
   Score: 14.8204
   Content: ## Delivery timeframes
- Standard delivery: 7–10 business days; free for all cardholders.
- Expedited shipping: 2–3 business days.

## Expedited shipping fees by card tier
- Entry-tier (Bronze Rewards Card, EcoCard, Business Bronze Rewards Card): $15.00.
- Mid-tier (Silver Rewards Card, Business Silver Rewards Card, Green Rewards Card, Silver Zoom Card): $10.00.
- Premium-tier and above (Gold Rewards Card, Business Gold Rewards Card, Platinum Rewards Card, Business Platinum Rewards Card, Diamond Elite Card): $0.00 (complimentary).

## When to choose expedited shipping
- If your card was stolen or you suspect fraud, we strongly recommend expedited shipping to reduce the window for potential misuse.
- If you have upcoming travel or urgent payment needs, expedited shipping can help ensure you receive your card within the accelerated timeframe noted above.

8. Business Bronze Saver: Complete Guide
   ID: doc_business_savings_accounts_bronze_saver_account_001
   Score: 14.3573
   Content: ## Account Snapshot

- APY: 2.0%
- Monthly maintenance fee: $0.00
- Minimum opening deposit: $0
- Ongoing minimum balance: Not required
- Withdrawals: Generous monthly limits designed for frequent access

## Opening Your Account

1. Start your application online and select Business Bronze Saver.
2. Review and accept the account terms and disclosures.
3. Fund the account with at least $0 (you can open with $0 and add funds anytime).
4. Set your preferred funding source for future deposits and transfers.

Tips:
- If you plan to fund later, set up a reminder so your balance begins earning 2.0% as soon as funds arrive.
- Add authorized users who will help manage deposits and withdrawals.

## Funding and Earning Interest

- You earn 2.0% on your available balance.
- Make deposits via transfer from your business banking source of choice.
- Larger, less frequent deposits generally help you maintain a higher average balance, which increases your total interest earned at the same APY.

Best practices:
- Schedule periodic transfers that match your cash-flow cycle (weekly, biweekly, or monthly).
- Keep funds in the account for as long as possible during the month to maximize interest at 2.0%.

## APY Bonuses with Business Rewards Cards

If you hold an eligible Business Rewards Card, your APY increases by the corresponding bonus. The bonus is added to 2.0%.

- Business Silver Rewards Card: 0.15% (approx. total APY 2.15%)
- Business Gold Rewards Card: 0.35% (approx. total APY 2.35%)
- Business Platinum Rewards Card: 0.65% (approx. total APY 2.65%)

How to apply the bonus:
- Ensure your card is active and in the same business profile as your savings account.
- The APY bonus reflects automatically once eligibility is recognized.

## Managing Withdrawals

- Initiate withdrawals through your online banking transfers.
- Plan multiple smaller withdrawals within the generous monthly limit if you foresee periodic cash needs.
- When moving larger sums, consider consolidating into fewer transfers to stay comfortably within the monthly allowance.
- Schedule withdrawals toward the end of your billing cycle when possible to keep funds earning 2.0% longer.

## Example Earnings

Approximate annual interest if your average balance remains constant:

- $10,000 average balance
  - Base APY 2.0%: about $200/year
  - With Business Silver Rewards Card bonus: about $215/year
  - With Business Gold Rewards Card bonus: about $235/year
  - With Business Platinum Rewards Card bonus: about $265/year

- $25,000 average balance
  - Base APY 2.0%: about $500/year
  - With Business Silver Rewards Card bonus: about $537.50/year
  - With Business Gold Rewards Card bonus: about $587.50/year
  - With Business Platinum Rewards Card bonus: about $662.50/year

These estimates assume the APY remains the same and the balance does not change during the period.

## Common Questions

- Is there a monthly maintenance fee?
  - No. The monthly maintenance fee is $0.00.

- What is the minimum to open the account?
  - $0. You can open now and fund later.

- How do the APY bonuses work with cards?
  - If you hold an eligible Business Rewards Card, your APY increases by the applicable bonus: 0.15%, 0.35%, or 0.65%.

9. Platinum Account: Credit Card APY Bonuses
   ID: doc_savings_accounts_platinum_account_010
   Score: 14.2148
   Content: ## Credit card APY bonuses for Platinum Account holders

Holding certain Rho-Bank credit cards provides bonus APY on your Platinum Account balance. These bonuses are automatically applied when you hold both the credit card and savings account under the same customer profile.

### Available credit card APY bonuses

| Credit Card | APY Bonus |
|---|---|
| Bronze Rewards Card | +0% |
| Silver Rewards Card | +0% |
| Gold Rewards Card | +0.15% |
| Platinum Rewards Card | +0.25% |
| Diamond Elite Card | +0.35% |
| EcoCard | +0% |
| Green Rewards Card | +0% |
| Crypto-Cash Back Card | +0% |

### How to qualify

1. Open or maintain a Platinum Account.
2. Hold an eligible Rho-Bank credit card under the same customer profile.
3. The APY bonus is automatically applied to your Platinum Account earnings.

10. Platinum Plus Account: Credit Card APY Bonuses
   ID: doc_savings_accounts_platinum_plus_account_009
   Score: 14.1196
   Content: ## Credit card APY bonuses for Platinum Plus Account holders

Holding certain Rho-Bank credit cards provides bonus APY on your Platinum Plus Account balance. These bonuses are automatically applied when you hold both the credit card and savings account under the same customer profile.

### Available credit card APY bonuses

| Credit Card | APY Bonus |
|---|---|
| Bronze Rewards Card | +0% |
| Silver Rewards Card | +0% |
| Gold Rewards Card | +0.1% |
| Platinum Rewards Card | +0.4% |
| Diamond Elite Card | +0.6% |
| EcoCard | +0.05% |
| Green Rewards Card | +0% |
| Crypto-Cash Back Card | +0.25% |

### How to qualify

1. Open or maintain a Platinum Plus Account.
2. Hold an eligible Rho-Bank credit card under the same customer profile.
3. The APY bonus is automatically applied to your Platinum Plus Account earnings.


[Timing: retrieval=3ms, reranking=0ms, total=3ms]

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "id": "skill-13",
  "role": "tool",
  "requestor": "assistant",
  "error": false,
  "turn_idx": 27,
  "timestamp": "2026-11-15T01:53:09.292223"
}
```


</details>

<a id="m028"></a>

### M028 · assistant

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "skill-14",
      "name": "KB_search",
      "arguments": {
        "query": "Cobalt Blue account referral program reward bonus"
      },
      "requestor": "assistant"
    }
  ],
  "is_audio": false,
  "turn_idx": 28,
  "timestamp": "2026-11-15T01:53:09.304536",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 0.011196102001122199,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m029"></a>

### M029 · tool

1. True Blue Account: Fee Waivers and Balance Requirements
   ID: doc_business_checking_accounts_true_blue_002
   Score: 16.7387
   Content: ## Waiving your monthly maintenance fee
- You will be charged $75.00 each month unless you meet the waiver threshold.
- The monthly maintenance fee is waived when your balance is at least $50,000 during the statement period.

## Minimum balance requirement vs. fee waiver threshold
- Minimum balance requirement: $25,000 to maintain the account and access premium features.
- Fee waiver threshold: $50,000 to waive the $75.00 monthly maintenance fee.
- Falling below $25,000 may limit access to premium features until your balance is restored.

## Overdrafts and shortfalls
- If your balance goes negative, a per-occurrence overdraft fee of $25.00 may apply.

## How to avoid fees
- Maintain a balance of at least $50,000 to waive the monthly maintenance fee.
- Set internal processes to monitor balances against both $25,000 and $50,000.
- If a shortfall is anticipated, transfer funds promptly to avoid the $25.00 and preserve eligibility for the fee waiver.

## True Blue Referral Program

Refer other high-volume businesses to True Blue and earn significant rewards:

| Benefit | Amount |
| --- | --- |
| Referrer bonus | $350 per referral |
| New member bonus | $250 |
| Maximum referrals per year | 15 |
| Qualifying deposit | $50,000 |
| Deposit window | 120 days |
| Account age requirement | 90 days |

### Referral requirements
- The referred business must deposit $50,000 within 120 days of opening their True Blue account.
- Eligibility is based on how long you've been a Rho-Bank checking customer. The account age threshold is 90 days, calculated from when you opened your oldest checking account.
- Referral bonuses are paid after qualification is confirmed and are subject to the annual limit of 15.

2. Silver Zoom Card: Referral Program - Earn Rewards for Referring Logistics Businesses
   ID: doc_business_credit_cards_silver_zoom_card_011
   Score: 15.5596
   Content: ## How the referral program works
- Earn a referral bonus of $150 for each referred logistics business that is approved and meets the qualifying spend requirement
- Bonuses are capped at 10 per calendar year

## Qualifying activity for your referral
- The referred business must complete purchases totaling $7,500 within 90 days of account opening
- Only one referrer is credited per approved account

## Program timing
- No new referrals are accepted after 2025-10-01

## How to refer
- Share your referral link or submit the referral through your account portal before the referred business applies
- Ensure the referred business uses your link or is otherwise properly attributed during application
- Track referral status within your account until the qualifying spend threshold of $7,500 is met

## Payout details
- Bonuses are typically issued to the referrer after the referred business satisfies the $7,500 requirement within 90 days
- If the referred business returns purchases or does not meet the requirement, no bonus is issued

3. Business Gold Rewards Card: Referral Program - Earn Rewards for Referring Businesses
   ID: doc_business_credit_cards_business_gold_rewards_card_010
   Score: 14.9519
   Content: ## How the Referral Bonus Works
- Earn $200 for each successful referral who is approved and meets the qualifying spend.
- You can earn up to 8 referral bonuses per calendar year.

## Qualifying Spend Requirement
- The referred business must spend $7,500 within 90 from account opening to qualify your bonus.

## Program Timeline
- The referral program accepts new referrals until 2025-09-15. Referrals submitted after this date are not eligible.

## How to Refer
- Generate your unique referral link from your account’s referral center.
- Share the link directly with businesses that consent to receive it.
- Track application status and eligibility in the referral dashboard.

## Payouts
- Once the referred account is approved and completes $7,500 within 90, your $200 is queued for issuance to your account.

## Rules and Best Practices
- Self-referrals are not permitted.
- Share referral invitations only with contacts who have given permission to receive them.
- If a referral applies without your link, the referral may not be attributed.
- Program terms, eligible industries, and promotional availability may change without notice prior to 2025-09-15.

4. Navy Blue Business Checking: Complete Guide
   ID: doc_business_checking_accounts_navy_blue_001
   Score: 14.8947
   Content: ## Key Account Costs and Limits

- Monthly maintenance fee: $0.00
- Annual Percentage Yield (APY) on balances: 0.5%
- Daily digital transfer limit: $25,000

### What you can expect day to day
- No minimum balance requirement, so you can use the account flexibly.
- Unlimited digital transfers within the daily limit of $25,000.
- Optional overdraft settings are available if you want coverage on eligible transactions.
- E-statements are included at no additional cost.

### Practical tips for managing your account
- Use e-statements to keep records organized and accessible.
- Plan larger transfers with the daily limit of $25,000 in mind; schedule across days if needed.
- Keep an eye on your balance to maximize earnings at 0.5%.

### Quick reference
| Item | Amount |
| --- | --- |
| Monthly maintenance fee | $0.00 |
| APY | 0.5% |
| Daily digital transfer limit | $25,000 |

## Business Referral Program

Grow your network and earn rewards by referring other businesses to Navy Blue:

| Referral Detail | Value |
| --- | --- |
| Your referral bonus | $100 |
| New business welcome bonus | $75 |
| Maximum referrals per year | 10 |
| Required qualifying deposit | $5,000 |
| Deposit must be made within | 90 days |
| Your account age requirement | 60 days |

To qualify: The referred business must open a Navy Blue account and deposit at least $5,000 within 90 days of account opening. Referrer eligibility requires having been a Rho-Bank checking customer for 60 days or more.

5. Beige Account Referral Program
   ID: doc_business_checking_accounts_beige_012
   Score: 14.6312
   Content: ## Enterprise referral program

Refer other enterprise-level businesses to the Beige Account and earn premium referral rewards.

### Premium rewards
- **Your reward**: $500 for each qualifying referral
- **Their reward**: $350 welcome bonus
- **Annual maximum**: 15 referral bonuses per calendar year

### Qualification criteria
To earn a referral bonus:
1. Referrer tenure requirement: 120 days since opening your first checking account with us.
2. The referred enterprise must open a Beige Account
3. They must deposit at least $100,000 within 120 days

### Referral details
| Detail | Amount |
|---|---|
| Referrer bonus | $500 |
| Referred bonus | $350 |
| Maximum per year | 15 |
| Required deposit | $100,000 |
| Deposit window | 120 days |
| Minimum tenure | 120 days |

### How to participate
1. Contact your dedicated relationship manager for referral materials
2. Introduce qualified enterprises to the Beige Account benefits
3. Your relationship manager can facilitate introductions and track referrals
4. Bonuses are credited after all qualification requirements are confirmed

### Enterprise considerations
- Referrals must be for new Beige Account relationships
- Both enterprises must maintain accounts in good standing
- Premium referral bonuses reflect the enterprise-level relationship value

6. Gold Years Account Referral Program
   ID: doc_checking_accounts_gold_years_account_010
   Score: 14.3974
   Content: ## Refer a friend to Gold Years

Share the benefits of the Gold Years Account with friends and family members who are 62 or older.

### Rewards
- **You receive**: $50 for each successful referral
- **They receive**: $75 as a welcome bonus
- **Annual maximum**: 6 referral bonuses per calendar year

### How to qualify
- The referrer must have maintained checking account status with Rho-Bank for 30 days.
- The person you refer must be eligible for a Gold Years Account (age 62+)
- They must deposit $1,000 within 90 days of account opening

### Referral summary
| Program element | Detail |
|---|---|
| Your bonus | $50 |
| Their bonus | $75 |
| Max referrals/year | 6 |
| Qualifying deposit | $1,000 |
| Deposit deadline | 90 days |
| Customer tenure | 30 days |

### Getting started
1. Find your personalized referral link in your account settings
2. Share it with eligible friends and family
3. Track successful referrals in your rewards dashboard

7. Dark Green Account Referral Program
   ID: doc_checking_accounts_dark_green_account_010
   Score: 14.2872
   Content: ## Share the Dark Green experience

Refer others to the Dark Green Account and earn rewards when they join.

### Referral rewards
- **Your bonus**: $40 for each qualifying referral
- **Their bonus**: $30 welcome bonus
- **Maximum per year**: 6 referral bonuses

### Qualification criteria
To qualify for the referral bonus:
1. You must satisfy the 45-day minimum as a Rho-Bank checking customer.
2. The person you refer must open a Dark Green Account
3. They must deposit at least $1,000 within 60 days of opening

### Program details
| Aspect | Value |
|---|---|
| Referrer bonus | $40 |
| Referred bonus | $30 |
| Annual cap | 6 referrals |
| Minimum deposit | $1,000 |
| Deposit window | 60 days |
| Tenure required | 45 days |

### Bonus payment
- Bonuses are credited within 5-7 business days after qualification
- Both you and the new member must maintain your accounts in good standing

8. Business Silver Rewards Card: Referral Program - Earn Rewards for Referring Businesses
   ID: doc_business_credit_cards_business_silver_rewards_card_013
   Score: 14.0141
   Content: ## What you can earn
- Earn $100 for each successful referral that is approved and meets the qualifying spend requirement
- You can earn up to 10 referral bonuses per calendar year

## Qualifying spend requirement
- The referred business must spend at least $3,000 within 90 days of account opening for you to receive the bonus

## How to refer
- Share a referral through the official referral channel so applications are tracked correctly
- Ensure the referred business uses your referral details when applying

## Tracking and payout
- After the referred business is approved and completes the qualifying spend, your $100 bonus will be processed according to program rules
- If a referral does not appear, contact support with the referred business name and application date so it can be investigated

9. Internal: Understanding Credit Card Referral Statuses.
   ID: doc_credit_cards_credit_cards_(general)_001
   Score: 13.9980
   Content: ## Referral status meanings

- COMPLETE — the referred person has successfully opened a new account and met the criteria to get the referral bonus
- IN_PROGRESS — the referred person has successfully opened a new account and is in progress to meet the criteria for the referral bonus
- NO_PROGRESS — the referred person has not applied yet, no progress has been made
- APPLIED — the referred person has sent in the application and is waiting for a decision
- REJECTED — the user has too many referral processes going on
- ERROR — an error has occurred throughout the process

### How to interpret and act
- COMPLETE: The bonus will be granted per the applicable referral program terms.
- IN_PROGRESS: No action required; monitor until criteria are met.
- NO_PROGRESS: You may remind the referrer that the invitee has not started an application.
- APPLIED: Await the application decision; no manual intervention is needed.
- REJECTED: Do not retry immediately; review the user’s existing referral activity before advising next steps.
- ERROR: Retry later or escalate internally if the condition persists.

10. Refer a Friend to Rho-Bank and Earn Rewards
   ID: doc_credit_cards_credit_cards_(general)_020
   Score: 13.7897
   Content: Do you love your Rho-Bank credit card? Share the love with friends and family, and you could both earn rewards! Our referral program makes it easy to invite the people you care about to join Rho-Bank, and when they're approved for a new card and meet the program requirements, you'll both be rewarded.

## How It Works

Participating in our referral program is simple. When you refer someone to apply for a Rho-Bank credit card and they're approved, you may be eligible to receive a referral bonus. The specific bonus amount and requirements vary depending on which credit card you're referring them to—some cards offer cash back bonuses, while others may offer bonus points or statement credits.

## Getting Your Referral Link

To refer a friend, you'll need to generate a unique referral link that's tied to your account. You can do this through the Rho-Bank mobile app, online banking portal, or by contacting our customer service team. Once you have your link, simply share it with friends and family via email, text, or social media. When they use your link to apply and are approved, the referral will be tracked to your account.

## Important Things to Know

To ensure the referral program remains fair for all participants, there are a few guidelines to keep in mind:

- **Weekly Limit**: You can earn referral bonuses for up to 2 successful referrals per week. This is calculated on a rolling 7-day basis, so if you've already had 2 referrals complete in the past week, any additional referrals during that time won't qualify for a bonus.
- **Eligibility**: Not all credit cards participate in the referral program. Before sharing your link, make sure the card you're referring has an active referral offer.
- **Bonus Requirements**: Each referral program has specific requirements that your friend must meet to trigger the bonus, such as making a certain amount of purchases within a specified timeframe after account opening.

## Check Your Referral Status

You can track the status of your referrals at any time through the Rho-Bank mobile app or by contacting customer service. We'll also send you notifications when your referrals are approved and when you earn your bonus.

If you have any questions about the referral program or want to confirm the current offer for your card, please reach out to our customer service team at 1-800-RHO-BANK. We're always happy to help!


[Timing: retrieval=2ms, reranking=0ms, total=2ms]

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "id": "skill-14",
  "role": "tool",
  "requestor": "assistant",
  "error": false,
  "turn_idx": 29,
  "timestamp": "2026-11-15T01:53:09.307980"
}
```


</details>

<a id="m030"></a>

### M030 · assistant

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "skill-15",
      "name": "KB_search",
      "arguments": {
        "query": "referral link generate checking account get_referral_link user_id account name"
      },
      "requestor": "assistant"
    }
  ],
  "is_audio": false,
  "turn_idx": 30,
  "timestamp": "2026-11-15T01:53:23.306175",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 13.997235468006693,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m031"></a>

### M031 · tool

1. Generating a Credit Card Referral Link (Internal)
   ID: doc_credit_cards_credit_cards_(general)_009
   Score: 21.8629
   Content: ## Pre-check before providing the referral tool
- Search the knowledge base to confirm the specific card has a documented referral program.
- Verify the customer’s understanding of referral terms. If the customer cites terms that do not match any documented program, clarify the discrepancy.
- If no referral program is documented for the requested card, or if the user’s claimed terms are incorrect, or if there is reason to believe the referral will be automatically rejected, explain why and do not provide a referral link tool. Do not transfer to a human in these cases.

## How the user generates their referral link
- Provide the customer with this tool and instruct them to run it themselves:
  - `get_referral_link(user_id: str, card_name: str)`
- Tell the customer to pass their own user_id and the exact card name (for example, 'Gold Rewards Card').
- When the tool is called successfully, a referral record is created with status 'NO_PROGRESS'. The referred person can then use the generated link to apply.

## Important reminders
- Weekly limit: Customers can receive at most 2 referral bonuses in any rolling 7-day window; the third and subsequent referrals in that window are automatically denied.
- Agents must not generate the link on the customer’s behalf.
- Reiterate the correct referral terms as documented to prevent confusion and complaints.

2. Business Gold Rewards Card: Referral Program - Earn Rewards for Referring Businesses
   ID: doc_business_credit_cards_business_gold_rewards_card_010
   Score: 18.8629
   Content: ## How the Referral Bonus Works
- Earn $200 for each successful referral who is approved and meets the qualifying spend.
- You can earn up to 8 referral bonuses per calendar year.

## Qualifying Spend Requirement
- The referred business must spend $7,500 within 90 from account opening to qualify your bonus.

## Program Timeline
- The referral program accepts new referrals until 2025-09-15. Referrals submitted after this date are not eligible.

## How to Refer
- Generate your unique referral link from your account’s referral center.
- Share the link directly with businesses that consent to receive it.
- Track application status and eligibility in the referral dashboard.

## Payouts
- Once the referred account is approved and completes $7,500 within 90, your $200 is queued for issuance to your account.

## Rules and Best Practices
- Self-referrals are not permitted.
- Share referral invitations only with contacts who have given permission to receive them.
- If a referral applies without your link, the referral may not be attributed.
- Program terms, eligible industries, and promotional availability may change without notice prior to 2025-09-15.

3. Light Blue Account Referral Program
   ID: doc_checking_accounts_light_blue_account_007
   Score: 17.7142
   Content: ## Earn rewards by referring friends

Share the Light Blue Account with others and earn cash bonuses.

### What you earn
- Referral bonus: $30 for each successful referral
- Maximum referrals: 5 per calendar year

### What they receive
- Welcome bonus: $20 when they open and fund their account

### Requirements

| Requirement | Detail |
|---|---|
| Qualifying deposit | $500 |
| Deposit window | Within 60 days of account opening |
| Referrer tenure | 30 days |

### How it works
1. Share your unique referral link with friends and family
2. They open a Light Blue Account using your link
3. They deposit at least $500 within 60 days
4. You receive $30 and they receive $20

### Eligibility
- To qualify as a referrer, you must have been a Rho-Bank checking account holder for 30 days or longer.
- You can earn up to 5 referral bonuses per calendar year

4. Gold Years Account Referral Program
   ID: doc_checking_accounts_gold_years_account_010
   Score: 15.9867
   Content: ## Refer a friend to Gold Years

Share the benefits of the Gold Years Account with friends and family members who are 62 or older.

### Rewards
- **You receive**: $50 for each successful referral
- **They receive**: $75 as a welcome bonus
- **Annual maximum**: 6 referral bonuses per calendar year

### How to qualify
- The referrer must have maintained checking account status with Rho-Bank for 30 days.
- The person you refer must be eligible for a Gold Years Account (age 62+)
- They must deposit $1,000 within 90 days of account opening

### Referral summary
| Program element | Detail |
|---|---|
| Your bonus | $50 |
| Their bonus | $75 |
| Max referrals/year | 6 |
| Qualifying deposit | $1,000 |
| Deposit deadline | 90 days |
| Customer tenure | 30 days |

### Getting started
1. Find your personalized referral link in your account settings
2. Share it with eligible friends and family
3. Track successful referrals in your rewards dashboard

5. Business Bronze Rewards Card: Referral Program - Earn Rewards for Referring Businesses
   ID: doc_business_credit_cards_business_bronze_rewards_card_011
   Score: 15.6736
   Content: ## What You Can Earn
- Receive $75 for each successful referral.
- You can earn up to 7 referral bonuses per calendar year.

## What Makes a Referral Successful
- The referred business must be approved for the card.
- The referred business must complete at least $1,750 in net purchases within 90 days of account opening.

## How to Refer
1. Share your referral link or code with another business.
2. Ensure they apply using your link or enter your code during their application.
3. You will be notified when the referral is approved and has met the $1,750 requirement within 90 days.

## Tracking Your Bonuses
- Monitor referral status, qualifying spend progress, and paid bonuses in your account dashboard.
- If a referred account is closed or reversed, any unpaid referral bonus may be canceled.

## Best Practices
- Encourage referrals to complete their initial purchases early to meet the $1,750 requirement within 90 days.
- Remind referrals to use your link or code so your bonus is tracked correctly.

6. Green Fee-Free Account Referral Program
   ID: doc_checking_accounts_green_fee-free_account_007
   Score: 15.5836
   Content: ## Refer and earn

Help others discover the Green Fee-Free Account and earn rewards for successful referrals.

### Bonus structure
- Your reward: $20 per successful referral
- New member reward: $35 welcome bonus
- Annual limit: 4 referrals per year

### Qualification requirements
For a referral to count as successful:
- The new account holder must deposit at least $300
- This deposit must be made within 60 days of opening their account
- Your Rho-Bank checking relationship must span at least 30 days.

### Quick reference
| Detail | Amount |
|---|---|
| You earn | $20 |
| They earn | $35 |
| Max per year | 4 |
| Required deposit | $300 |
| Deposit deadline | 60 days |
| Referrer eligibility | 30 days |

### How to participate
1. Access your referral link from your account dashboard
2. Share with potential new members
3. Track your referrals and bonuses in the rewards section

7. Silver Zoom Card: Referral Program - Earn Rewards for Referring Logistics Businesses
   ID: doc_business_credit_cards_silver_zoom_card_011
   Score: 15.4256
   Content: ## How the referral program works
- Earn a referral bonus of $150 for each referred logistics business that is approved and meets the qualifying spend requirement
- Bonuses are capped at 10 per calendar year

## Qualifying activity for your referral
- The referred business must complete purchases totaling $7,500 within 90 days of account opening
- Only one referrer is credited per approved account

## Program timing
- No new referrals are accepted after 2025-10-01

## How to refer
- Share your referral link or submit the referral through your account portal before the referred business applies
- Ensure the referred business uses your link or is otherwise properly attributed during application
- Track referral status within your account until the qualifying spend threshold of $7,500 is met

## Payout details
- Bonuses are typically issued to the referrer after the referred business satisfies the $7,500 requirement within 90 days
- If the referred business returns purchases or does not meet the requirement, no bonus is issued

8. Silver Rewards Card: Referral Program - Earn Rewards for Referring Friends
   ID: doc_credit_cards_silver_rewards_card_011
   Score: 15.0383
   Content: ## What You Earn
- Receive 75 for each successful referral
- You can earn up to 7 referral bonuses per calendar year

## What Your Referral Must Do
- The referred person must be approved and spend at least $750 within 60 days of account opening

## How to Refer
1. Share your referral link or code with friends and colleagues
2. Ensure they apply using your link or code so the referral is tracked
3. You’ll be notified when the referral meets the qualifying spend requirement

## Payout Timing
- Your bonus typically posts within one to two billing cycles after the referred account meets the $750 requirement

## Program Tips
- Remind your referral to activate their card promptly and add recurring bills to help them meet $750 within 60 days
- Track your annual count to stay within the 7 limit

9. EcoCard: Referral Program - Earn Rewards for Referring Friends
   ID: doc_credit_cards_ecocard_011
   Score: 15.0383
   Content: ## What You Earn
- Receive 50 for each successful referral
- You can earn up to 7 referral bonuses per calendar year

## What Your Referral Must Do
- The referred person must be approved and spend at least $500 within 60 days of account opening

## How to Refer
1. Share your referral link or code with friends and family
2. Ensure they apply using your link or code so the referral is tracked
3. You'll be notified when the referral meets the qualifying spend requirement

## Payout Timing
- Your bonus typically posts within one to two billing cycles after the referred account meets the $500 requirement

## Program Tips
- Remind your referral to activate their card promptly and add recurring bills to help them meet $500 within 60 days
- Track your annual count to stay within the 7 limit

10. Light Green Account specifications and requirements
   ID: doc_checking_accounts_light_green_account_002
   Score: 14.7315
   Content: ## Eligibility requirements
- You must be the primary account holder and be between 13 and 24 years old to open the account.
- You must remain within the 13–24 age range to maintain the account.

### Age verification and ongoing eligibility
- Your eligibility is determined using your date of birth at account opening and on an ongoing basis.
- Once you are no longer within the 13–24 range, you are no longer eligible to maintain the Light Green Account.

## Key specifications
- Overdraft fees: None (no overdraft fee is charged on this account)

## Rates
- Interest earned: 0.05% APY on the account balance

## Fees and limits
| Item | Amount/Limit |
|---|---|
| Monthly maintenance fee | $0.00 |
| Returned deposit fee (per returned item) | $12.50 |
| Incoming domestic wire transfer fee (per incoming wire) | $10.00 |
| Debit card daily purchase limit | $250 per day |

## Linked savings APY boosts
- If you link a Platinum Savings Account, you receive a 0.65% APY boost on that savings account.
- If you link a Diamond Elite Savings Account, you receive a 0.2% APY boost on that savings account.

## Referral program requirements
To participate in the Light Green Account referral program:
- The person you refer must deposit at least $100 within 90 days of opening their account.
- Referrer eligibility is based on account tenure: you must have opened your first Rho-Bank checking account at least 14 days ago.


[Timing: retrieval=2ms, reranking=0ms, total=2ms]

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "id": "skill-15",
  "role": "tool",
  "requestor": "assistant",
  "error": false,
  "turn_idx": 31,
  "timestamp": "2026-11-15T01:53:23.309306"
}
```


</details>

<a id="m032"></a>

### M032 · assistant

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "skill-16",
      "name": "KB_search",
      "arguments": {
        "query": "Cobalt Blue earn referral bonus dollars per referral"
      },
      "requestor": "assistant"
    }
  ],
  "is_audio": false,
  "turn_idx": 32,
  "timestamp": "2026-11-15T01:53:23.318803",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 0.008956075005698949,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m033"></a>

### M033 · tool

1. Light Blue Account Referral Program
   ID: doc_checking_accounts_light_blue_account_007
   Score: 20.6135
   Content: ## Earn rewards by referring friends

Share the Light Blue Account with others and earn cash bonuses.

### What you earn
- Referral bonus: $30 for each successful referral
- Maximum referrals: 5 per calendar year

### What they receive
- Welcome bonus: $20 when they open and fund their account

### Requirements

| Requirement | Detail |
|---|---|
| Qualifying deposit | $500 |
| Deposit window | Within 60 days of account opening |
| Referrer tenure | 30 days |

### How it works
1. Share your unique referral link with friends and family
2. They open a Light Blue Account using your link
3. They deposit at least $500 within 60 days
4. You receive $30 and they receive $20

### Eligibility
- To qualify as a referrer, you must have been a Rho-Bank checking account holder for 30 days or longer.
- You can earn up to 5 referral bonuses per calendar year

2. True Blue Account: Fee Waivers and Balance Requirements
   ID: doc_business_checking_accounts_true_blue_002
   Score: 19.5113
   Content: ## Waiving your monthly maintenance fee
- You will be charged $75.00 each month unless you meet the waiver threshold.
- The monthly maintenance fee is waived when your balance is at least $50,000 during the statement period.

## Minimum balance requirement vs. fee waiver threshold
- Minimum balance requirement: $25,000 to maintain the account and access premium features.
- Fee waiver threshold: $50,000 to waive the $75.00 monthly maintenance fee.
- Falling below $25,000 may limit access to premium features until your balance is restored.

## Overdrafts and shortfalls
- If your balance goes negative, a per-occurrence overdraft fee of $25.00 may apply.

## How to avoid fees
- Maintain a balance of at least $50,000 to waive the monthly maintenance fee.
- Set internal processes to monitor balances against both $25,000 and $50,000.
- If a shortfall is anticipated, transfer funds promptly to avoid the $25.00 and preserve eligibility for the fee waiver.

## True Blue Referral Program

Refer other high-volume businesses to True Blue and earn significant rewards:

| Benefit | Amount |
| --- | --- |
| Referrer bonus | $350 per referral |
| New member bonus | $250 |
| Maximum referrals per year | 15 |
| Qualifying deposit | $50,000 |
| Deposit window | 120 days |
| Account age requirement | 90 days |

### Referral requirements
- The referred business must deposit $50,000 within 120 days of opening their True Blue account.
- Eligibility is based on how long you've been a Rho-Bank checking customer. The account age threshold is 90 days, calculated from when you opened your oldest checking account.
- Referral bonuses are paid after qualification is confirmed and are subject to the annual limit of 15.

3. FAQ: Blue Account
   ID: doc_checking_accounts_blue_account_010
   Score: 19.4119
   Content: ## Frequently asked questions

### What does a paper statement cost?
Paper statements are available for $2.50 per month.

### What APY do I earn on my balance?
Your Blue Account earns 0.01% APY on balances.

### Can I set low-balance alerts?
Yes. You can enable alerts at a threshold such as $62 so you are notified when your available balance reaches that level.

### How long do external bank transfers take?
Transfers to another bank typically complete in 2 business days.

### What happens if a deposited check is returned unpaid?
If a deposited check is returned by the issuing bank, a returned deposit fee of $15.00 applies.

### Is there a fee to receive a domestic wire?
Yes. Incoming domestic wires are assessed a fee of $12.50 per wire.

### Does the Blue Account have a referral program?
Yes. When you refer someone to open a Blue Account, you earn $35 for each successful referral. The person you refer receives $30 as a welcome bonus.

### What are the requirements for the referral bonus?
The referred person must deposit at least $500 within 60 days of opening their account. A minimum banking relationship of 30 days is required to participate—this is measured from when you first opened any checking account with us.

### Is there a limit to how many referral bonuses I can earn?
Yes. You can earn up to 5 referral bonuses per calendar year.

4. Business Silver Rewards Card: Referral Program - Earn Rewards for Referring Businesses
   ID: doc_business_credit_cards_business_silver_rewards_card_013
   Score: 19.2189
   Content: ## What you can earn
- Earn $100 for each successful referral that is approved and meets the qualifying spend requirement
- You can earn up to 10 referral bonuses per calendar year

## Qualifying spend requirement
- The referred business must spend at least $3,000 within 90 days of account opening for you to receive the bonus

## How to refer
- Share a referral through the official referral channel so applications are tracked correctly
- Ensure the referred business uses your referral details when applying

## Tracking and payout
- After the referred business is approved and completes the qualifying spend, your $100 bonus will be processed according to program rules
- If a referral does not appear, contact support with the referred business name and application date so it can be investigated

5. Beige Account Referral Program
   ID: doc_business_checking_accounts_beige_012
   Score: 18.8178
   Content: ## Enterprise referral program

Refer other enterprise-level businesses to the Beige Account and earn premium referral rewards.

### Premium rewards
- **Your reward**: $500 for each qualifying referral
- **Their reward**: $350 welcome bonus
- **Annual maximum**: 15 referral bonuses per calendar year

### Qualification criteria
To earn a referral bonus:
1. Referrer tenure requirement: 120 days since opening your first checking account with us.
2. The referred enterprise must open a Beige Account
3. They must deposit at least $100,000 within 120 days

### Referral details
| Detail | Amount |
|---|---|
| Referrer bonus | $500 |
| Referred bonus | $350 |
| Maximum per year | 15 |
| Required deposit | $100,000 |
| Deposit window | 120 days |
| Minimum tenure | 120 days |

### How to participate
1. Contact your dedicated relationship manager for referral materials
2. Introduce qualified enterprises to the Beige Account benefits
3. Your relationship manager can facilitate introductions and track referrals
4. Bonuses are credited after all qualification requirements are confirmed

### Enterprise considerations
- Referrals must be for new Beige Account relationships
- Both enterprises must maintain accounts in good standing
- Premium referral bonuses reflect the enterprise-level relationship value

6. Business Platinum Rewards Card: Referral Program - Earn Rewards for Referring Businesses
   ID: doc_business_credit_cards_business_platinum_rewards_card_012
   Score: 18.4260
   Content: ## How the Referral Bonus Works
- Share your referral through the designated channel. When the referred business is approved and completes qualifying spend of $15,000 within 135 days from account opening, you earn a bonus of $300.

## Annual Limits
- You can earn up to 11 referral bonuses per calendar year.

## Qualification Tips
- Encourage the referred business to use the card for eligible purchases promptly after activation to meet $15,000 within the allowed period.
- Ensure the referral is submitted before the application so it is properly attributed.

## Payout and Compliance
- Bonuses are credited to your account after verification that approval and qualifying spend requirements have been met.
- Referrals should comply with applicable marketing and solicitation rules; only share referral information with contacts who have consented to receive it.

7. Earning Interest on Your World Blue Balance
   ID: doc_business_checking_accounts_world_blue_007
   Score: 18.1852
   Content: ## Rate and compounding
- Your USD balance earns an Annual Percentage Yield of 1.0%
- Interest is compounded daily

## How interest is applied
- Interest accrues on eligible USD funds held in the account and is credited in accordance with your statement cycle
- If you move funds between currencies, only USD balances accrue interest at 1.0%

## Monitoring your earnings
- Track accrued and credited interest in your account activity and statements
- Export transaction data to reconcile interest income in your general ledger

## Tips for maximizing earned interest
- Keep operational reserves in USD when appropriate so they benefit from compounding daily
- Align conversion and payout timing with your cash needs so idle USD balances remain interest-earning as long as practicable

## Referral bonuses for World Blue members

In addition to interest earnings, you can earn rewards by referring other international businesses to World Blue:

- **Your bonus**: $300 for each successful referral
- **Their bonus**: $200 welcome bonus for the new business
- **Annual limit**: 12 referral bonuses per calendar year

Referral bonuses are typically credited within 7-10 business days of qualification. Both accounts must remain in good standing for bonuses to be paid.


8. Silver Rewards Card: Referral Program - Earn Rewards for Referring Friends
   ID: doc_credit_cards_silver_rewards_card_011
   Score: 17.9814
   Content: ## What You Earn
- Receive 75 for each successful referral
- You can earn up to 7 referral bonuses per calendar year

## What Your Referral Must Do
- The referred person must be approved and spend at least $750 within 60 days of account opening

## How to Refer
1. Share your referral link or code with friends and colleagues
2. Ensure they apply using your link or code so the referral is tracked
3. You’ll be notified when the referral meets the qualifying spend requirement

## Payout Timing
- Your bonus typically posts within one to two billing cycles after the referred account meets the $750 requirement

## Program Tips
- Remind your referral to activate their card promptly and add recurring bills to help them meet $750 within 60 days
- Track your annual count to stay within the 7 limit

9. EcoCard: Referral Program - Earn Rewards for Referring Friends
   ID: doc_credit_cards_ecocard_011
   Score: 17.9814
   Content: ## What You Earn
- Receive 50 for each successful referral
- You can earn up to 7 referral bonuses per calendar year

## What Your Referral Must Do
- The referred person must be approved and spend at least $500 within 60 days of account opening

## How to Refer
1. Share your referral link or code with friends and family
2. Ensure they apply using your link or code so the referral is tracked
3. You'll be notified when the referral meets the qualifying spend requirement

## Payout Timing
- Your bonus typically posts within one to two billing cycles after the referred account meets the $500 requirement

## Program Tips
- Remind your referral to activate their card promptly and add recurring bills to help them meet $500 within 60 days
- Track your annual count to stay within the 7 limit

10. Business Bronze Rewards Card: Referral Program - Earn Rewards for Referring Businesses
   ID: doc_business_credit_cards_business_bronze_rewards_card_011
   Score: 17.9477
   Content: ## What You Can Earn
- Receive $75 for each successful referral.
- You can earn up to 7 referral bonuses per calendar year.

## What Makes a Referral Successful
- The referred business must be approved for the card.
- The referred business must complete at least $1,750 in net purchases within 90 days of account opening.

## How to Refer
1. Share your referral link or code with another business.
2. Ensure they apply using your link or enter your code during their application.
3. You will be notified when the referral is approved and has met the $1,750 requirement within 90 days.

## Tracking Your Bonuses
- Monitor referral status, qualifying spend progress, and paid bonuses in your account dashboard.
- If a referred account is closed or reversed, any unpaid referral bonus may be canceled.

## Best Practices
- Encourage referrals to complete their initial purchases early to meet the $1,750 requirement within 90 days.
- Remind referrals to use your link or code so your bonus is tracked correctly.


[Timing: retrieval=2ms, reranking=0ms, total=2ms]

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "id": "skill-16",
  "role": "tool",
  "requestor": "assistant",
  "error": false,
  "turn_idx": 33,
  "timestamp": "2026-11-15T01:53:23.321612"
}
```


</details>

<a id="m034"></a>

### M034 · assistant

To get started, I need to verify your identity (this lets me check your account tenure and referral history, which determine what referral bonuses you're eligible for). Could you please provide:

1. Your full name (and user ID if you know it)
2. Any **two** of the following: date of birth, email address, phone number, or address on file

Once verified, I'll be able to tell you the best way to maximize your referral bonus.

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "is_audio": false,
  "turn_idx": 34,
  "timestamp": "2026-11-15T01:53:41.815285",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 18.49301412999921,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m035"></a>

### M035 · user

Sure! My name is Tomoko Ishikawa, and my user ID is ti87k4x9m2. My phone number is 206-555-3891 and my email is tomoko.ishikawa@seattletechconsult.com.

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "user",
  "is_audio": false,
  "turn_idx": 35,
  "timestamp": "2026-11-15T01:53:44.287511",
  "cost": 0.0,
  "usage": {
    "completion_tokens": 154,
    "prompt_tokens": 2264
  },
  "raw_data": {
    "id": "0217946788223460be08c7a69f2b84987924f53d1b93a4c91ea74",
    "created": 1794678824,
    "model": "deepseek-v4-flash-ga-260731",
    "object": "chat.completion",
    "system_fingerprint": null,
    "choices": [
      {
        "finish_reason": "stop",
        "index": 0,
        "message": {
          "content": "Sure! My name is Tomoko Ishikawa, and my user ID is ti87k4x9m2. My phone number is 206-555-3891 and my email is tomoko.ishikawa@seattletechconsult.com.",
          "role": "assistant",
          "tool_calls": null,
          "function_call": null,
          "reasoning_content": "The agent is asking for verification. I need to provide name and any two of the listed items. I'll give name, phone, email, and maybe DOB. They asked for two, but providing more is fine? The scenario says give name, phone, email, DOB, and/or address if asked. I'll provide full name and user ID if known - I know user_id ti87k4x9m2. And two others: phone and email. Let me provide naturally.",
          "provider_specific_fields": {
            "refusal": null,
            "reasoning_content": "The agent is asking for verification. I need to provide name and any two of the listed items. I'll give name, phone, email, and maybe DOB. They asked for two, but providing more is fine? The scenario says give name, phone, email, DOB, and/or address if asked. I'll provide full name and user ID if known - I know user_id ti87k4x9m2. And two others: phone and email. Let me provide naturally."
          }
        },
        "provider_specific_fields": {}
      }
    ],
    "usage": {
      "completion_tokens": 154,
      "prompt_tokens": 2264,
      "total_tokens": 2418,
      "completion_tokens_details": {
        "accepted_prediction_tokens": null,
        "audio_tokens": null,
        "reasoning_tokens": 101,
        "rejected_prediction_tokens": null,
        "text_tokens": null
      },
      "prompt_tokens_details": {
        "audio_tokens": null,
        "cache_write_tokens": null,
        "cached_tokens": 2048,
        "image_tokens": null,
        "text_tokens": null
      }
    },
    "metadata": null,
    "moderation": null,
    "service_tier": "default"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m036"></a>

### M036 · assistant

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "skill-17",
      "name": "get_user_information_by_id",
      "arguments": {
        "user_id": "ti87k4x9m2"
      },
      "requestor": "assistant"
    }
  ],
  "is_audio": false,
  "turn_idx": 36,
  "timestamp": "2026-11-15T01:53:48.197609",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 3.909729710998363,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m037"></a>

### M037 · tool

Found 1 record(s) in 'users':

1. Record ID: ti87k4x9m2
   name: Tomoko Ishikawa
   user_id: ti87k4x9m2
   address: 2847 Aurora Avenue North, Apt 12C, Seattle, WA 98103
   email: tomoko.ishikawa@seattletechconsult.com
   phone_number: 206-555-3891
   date_of_birth: 04/22/1987


<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "id": "skill-17",
  "role": "tool",
  "requestor": "assistant",
  "error": false,
  "turn_idx": 37,
  "timestamp": "2026-11-15T01:53:48.198377"
}
```


</details>

<a id="m038"></a>

### M038 · assistant

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "skill-18",
      "name": "log_verification",
      "arguments": {
        "name": "Tomoko Ishikawa",
        "user_id": "ti87k4x9m2",
        "address": "2847 Aurora Avenue North, Apt 12C, Seattle, WA 98103",
        "email": "tomoko.ishikawa@seattletechconsult.com",
        "phone_number": "206-555-3891",
        "date_of_birth": "04/22/1987",
        "time_verified": "2025-11-14 03:40:00 EST"
      },
      "requestor": "assistant"
    }
  ],
  "is_audio": false,
  "turn_idx": 38,
  "timestamp": "2026-11-15T01:53:56.107355",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 7.908462204999523,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m039"></a>

### M039 · tool

Verification logged successfully.
  - User: Tomoko Ishikawa (ID: ti87k4x9m2)
  - Verified at: 2025-11-14 03:40:00 EST

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "id": "skill-18",
  "role": "tool",
  "requestor": "assistant",
  "error": false,
  "turn_idx": 39,
  "timestamp": "2026-11-15T01:53:56.107949"
}
```


</details>

<a id="m040"></a>

### M040 · assistant

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "skill-19",
      "name": "get_referrals_by_user",
      "arguments": {
        "user_id": "ti87k4x9m2"
      },
      "requestor": "assistant"
    }
  ],
  "is_audio": false,
  "turn_idx": 40,
  "timestamp": "2026-11-15T01:53:56.115220",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 0.006400466998456977,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m041"></a>

### M041 · tool

No records found in 'referrals'.

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "id": "skill-19",
  "role": "tool",
  "requestor": "assistant",
  "error": false,
  "turn_idx": 41,
  "timestamp": "2026-11-15T01:53:56.116027"
}
```


</details>

<a id="m042"></a>

### M042 · assistant

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "skill-20",
      "name": "unlock_discoverable_agent_tool",
      "arguments": {
        "agent_tool_name": "get_all_user_accounts_by_user_id_3847"
      },
      "requestor": "assistant"
    }
  ],
  "is_audio": false,
  "turn_idx": 42,
  "timestamp": "2026-11-15T01:53:56.122327",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 0.0057957550015999,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m043"></a>

### M043 · tool

Tool unlocked: get_all_user_accounts_by_user_id_3847
Description: Retrieve all accounts (checking, savings, credit cards) for a customer.

Tool: get_all_user_accounts_by_user_id_3847
Description: Retrieve all accounts (checking, savings, credit cards) for a customer.
Parameters:
  - user_id: string (required) - The customer's unique identifier in the system

You can now use this tool by calling `call_discoverable_agent_tool` with agent_tool_name='get_all_user_accounts_by_user_id_3847' and the required arguments.

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "id": "skill-20",
  "role": "tool",
  "requestor": "assistant",
  "error": false,
  "turn_idx": 43,
  "timestamp": "2026-11-15T01:53:56.123219"
}
```


</details>

<a id="m044"></a>

### M044 · assistant

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "skill-21",
      "name": "call_discoverable_agent_tool",
      "arguments": {
        "agent_tool_name": "get_all_user_accounts_by_user_id_3847",
        "arguments": "{\"user_id\": \"ti87k4x9m2\"}"
      },
      "requestor": "assistant"
    }
  ],
  "is_audio": false,
  "turn_idx": 44,
  "timestamp": "2026-11-15T01:54:02.543319",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 6.4195712999935495,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m045"></a>

### M045 · tool

User accounts retrieved successfully.

Executed: get_all_user_accounts_by_user_id_3847
Accounts for user ti87k4x9m2:

Bank Accounts:
Found 2 record(s) in 'accounts':

1. Record ID: biz_ti87k4x9m2_worldblue
   account_id: biz_ti87k4x9m2_worldblue
   user_id: ti87k4x9m2
   class: business_checking
   level: World Blue Account
   date_opened: 09/10/2025
   status: OPEN
   current_holdings: 28000.00

2. Record ID: biz_ti87k4x9m2_cobaltblue
   account_id: biz_ti87k4x9m2_cobaltblue
   user_id: ti87k4x9m2
   class: business_checking
   level: Cobalt Blue Account
   date_opened: 10/01/2025
   status: OPEN
   current_holdings: 15000.00


Credit Card Accounts:
  No credit card accounts found.

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "id": "skill-21",
  "role": "tool",
  "requestor": "assistant",
  "error": false,
  "turn_idx": 45,
  "timestamp": "2026-11-15T01:54:02.544368"
}
```


</details>

<a id="m046"></a>

### M046 · assistant

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "skill-22",
      "name": "KB_search",
      "arguments": {
        "query": "Cobalt Blue Account complete guide referral program bonus amount"
      },
      "requestor": "assistant"
    }
  ],
  "is_audio": false,
  "turn_idx": 46,
  "timestamp": "2026-11-15T01:54:12.937375",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 10.392138126000646,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m047"></a>

### M047 · tool

1. True Blue Account: Fee Waivers and Balance Requirements
   ID: doc_business_checking_accounts_true_blue_002
   Score: 17.6416
   Content: ## Waiving your monthly maintenance fee
- You will be charged $75.00 each month unless you meet the waiver threshold.
- The monthly maintenance fee is waived when your balance is at least $50,000 during the statement period.

## Minimum balance requirement vs. fee waiver threshold
- Minimum balance requirement: $25,000 to maintain the account and access premium features.
- Fee waiver threshold: $50,000 to waive the $75.00 monthly maintenance fee.
- Falling below $25,000 may limit access to premium features until your balance is restored.

## Overdrafts and shortfalls
- If your balance goes negative, a per-occurrence overdraft fee of $25.00 may apply.

## How to avoid fees
- Maintain a balance of at least $50,000 to waive the monthly maintenance fee.
- Set internal processes to monitor balances against both $25,000 and $50,000.
- If a shortfall is anticipated, transfer funds promptly to avoid the $25.00 and preserve eligibility for the fee waiver.

## True Blue Referral Program

Refer other high-volume businesses to True Blue and earn significant rewards:

| Benefit | Amount |
| --- | --- |
| Referrer bonus | $350 per referral |
| New member bonus | $250 |
| Maximum referrals per year | 15 |
| Qualifying deposit | $50,000 |
| Deposit window | 120 days |
| Account age requirement | 90 days |

### Referral requirements
- The referred business must deposit $50,000 within 120 days of opening their True Blue account.
- Eligibility is based on how long you've been a Rho-Bank checking customer. The account age threshold is 90 days, calculated from when you opened your oldest checking account.
- Referral bonuses are paid after qualification is confirmed and are subject to the annual limit of 15.

2. Silver Zoom Card: Referral Program - Earn Rewards for Referring Logistics Businesses
   ID: doc_business_credit_cards_silver_zoom_card_011
   Score: 17.6409
   Content: ## How the referral program works
- Earn a referral bonus of $150 for each referred logistics business that is approved and meets the qualifying spend requirement
- Bonuses are capped at 10 per calendar year

## Qualifying activity for your referral
- The referred business must complete purchases totaling $7,500 within 90 days of account opening
- Only one referrer is credited per approved account

## Program timing
- No new referrals are accepted after 2025-10-01

## How to refer
- Share your referral link or submit the referral through your account portal before the referred business applies
- Ensure the referred business uses your link or is otherwise properly attributed during application
- Track referral status within your account until the qualifying spend threshold of $7,500 is met

## Payout details
- Bonuses are typically issued to the referrer after the referred business satisfies the $7,500 requirement within 90 days
- If the referred business returns purchases or does not meet the requirement, no bonus is issued

3. Refer a Friend to Rho-Bank and Earn Rewards
   ID: doc_credit_cards_credit_cards_(general)_020
   Score: 16.2883
   Content: Do you love your Rho-Bank credit card? Share the love with friends and family, and you could both earn rewards! Our referral program makes it easy to invite the people you care about to join Rho-Bank, and when they're approved for a new card and meet the program requirements, you'll both be rewarded.

## How It Works

Participating in our referral program is simple. When you refer someone to apply for a Rho-Bank credit card and they're approved, you may be eligible to receive a referral bonus. The specific bonus amount and requirements vary depending on which credit card you're referring them to—some cards offer cash back bonuses, while others may offer bonus points or statement credits.

## Getting Your Referral Link

To refer a friend, you'll need to generate a unique referral link that's tied to your account. You can do this through the Rho-Bank mobile app, online banking portal, or by contacting our customer service team. Once you have your link, simply share it with friends and family via email, text, or social media. When they use your link to apply and are approved, the referral will be tracked to your account.

## Important Things to Know

To ensure the referral program remains fair for all participants, there are a few guidelines to keep in mind:

- **Weekly Limit**: You can earn referral bonuses for up to 2 successful referrals per week. This is calculated on a rolling 7-day basis, so if you've already had 2 referrals complete in the past week, any additional referrals during that time won't qualify for a bonus.
- **Eligibility**: Not all credit cards participate in the referral program. Before sharing your link, make sure the card you're referring has an active referral offer.
- **Bonus Requirements**: Each referral program has specific requirements that your friend must meet to trigger the bonus, such as making a certain amount of purchases within a specified timeframe after account opening.

## Check Your Referral Status

You can track the status of your referrals at any time through the Rho-Bank mobile app or by contacting customer service. We'll also send you notifications when your referrals are approved and when you earn your bonus.

If you have any questions about the referral program or want to confirm the current offer for your card, please reach out to our customer service team at 1-800-RHO-BANK. We're always happy to help!

4. Internal: Understanding Credit Card Referral Statuses.
   ID: doc_credit_cards_credit_cards_(general)_001
   Score: 15.9992
   Content: ## Referral status meanings

- COMPLETE — the referred person has successfully opened a new account and met the criteria to get the referral bonus
- IN_PROGRESS — the referred person has successfully opened a new account and is in progress to meet the criteria for the referral bonus
- NO_PROGRESS — the referred person has not applied yet, no progress has been made
- APPLIED — the referred person has sent in the application and is waiting for a decision
- REJECTED — the user has too many referral processes going on
- ERROR — an error has occurred throughout the process

### How to interpret and act
- COMPLETE: The bonus will be granted per the applicable referral program terms.
- IN_PROGRESS: No action required; monitor until criteria are met.
- NO_PROGRESS: You may remind the referrer that the invitee has not started an application.
- APPLIED: Await the application decision; no manual intervention is needed.
- REJECTED: Do not retry immediately; review the user’s existing referral activity before advising next steps.
- ERROR: Retry later or escalate internally if the condition persists.

5. Navy Blue Business Checking: Complete Guide
   ID: doc_business_checking_accounts_navy_blue_001
   Score: 15.8411
   Content: ## Key Account Costs and Limits

- Monthly maintenance fee: $0.00
- Annual Percentage Yield (APY) on balances: 0.5%
- Daily digital transfer limit: $25,000

### What you can expect day to day
- No minimum balance requirement, so you can use the account flexibly.
- Unlimited digital transfers within the daily limit of $25,000.
- Optional overdraft settings are available if you want coverage on eligible transactions.
- E-statements are included at no additional cost.

### Practical tips for managing your account
- Use e-statements to keep records organized and accessible.
- Plan larger transfers with the daily limit of $25,000 in mind; schedule across days if needed.
- Keep an eye on your balance to maximize earnings at 0.5%.

### Quick reference
| Item | Amount |
| --- | --- |
| Monthly maintenance fee | $0.00 |
| APY | 0.5% |
| Daily digital transfer limit | $25,000 |

## Business Referral Program

Grow your network and earn rewards by referring other businesses to Navy Blue:

| Referral Detail | Value |
| --- | --- |
| Your referral bonus | $100 |
| New business welcome bonus | $75 |
| Maximum referrals per year | 10 |
| Required qualifying deposit | $5,000 |
| Deposit must be made within | 90 days |
| Your account age requirement | 60 days |

To qualify: The referred business must open a Navy Blue account and deposit at least $5,000 within 90 days of account opening. Referrer eligibility requires having been a Rho-Bank checking customer for 60 days or more.

6. Beige Account Referral Program
   ID: doc_business_checking_accounts_beige_012
   Score: 15.7149
   Content: ## Enterprise referral program

Refer other enterprise-level businesses to the Beige Account and earn premium referral rewards.

### Premium rewards
- **Your reward**: $500 for each qualifying referral
- **Their reward**: $350 welcome bonus
- **Annual maximum**: 15 referral bonuses per calendar year

### Qualification criteria
To earn a referral bonus:
1. Referrer tenure requirement: 120 days since opening your first checking account with us.
2. The referred enterprise must open a Beige Account
3. They must deposit at least $100,000 within 120 days

### Referral details
| Detail | Amount |
|---|---|
| Referrer bonus | $500 |
| Referred bonus | $350 |
| Maximum per year | 15 |
| Required deposit | $100,000 |
| Deposit window | 120 days |
| Minimum tenure | 120 days |

### How to participate
1. Contact your dedicated relationship manager for referral materials
2. Introduce qualified enterprises to the Beige Account benefits
3. Your relationship manager can facilitate introductions and track referrals
4. Bonuses are credited after all qualification requirements are confirmed

### Enterprise considerations
- Referrals must be for new Beige Account relationships
- Both enterprises must maintain accounts in good standing
- Premium referral bonuses reflect the enterprise-level relationship value

7. Business Gold Rewards Card: Referral Program - Earn Rewards for Referring Businesses
   ID: doc_business_credit_cards_business_gold_rewards_card_010
   Score: 14.9519
   Content: ## How the Referral Bonus Works
- Earn $200 for each successful referral who is approved and meets the qualifying spend.
- You can earn up to 8 referral bonuses per calendar year.

## Qualifying Spend Requirement
- The referred business must spend $7,500 within 90 from account opening to qualify your bonus.

## Program Timeline
- The referral program accepts new referrals until 2025-09-15. Referrals submitted after this date are not eligible.

## How to Refer
- Generate your unique referral link from your account’s referral center.
- Share the link directly with businesses that consent to receive it.
- Track application status and eligibility in the referral dashboard.

## Payouts
- Once the referred account is approved and completes $7,500 within 90, your $200 is queued for issuance to your account.

## Rules and Best Practices
- Self-referrals are not permitted.
- Share referral invitations only with contacts who have given permission to receive them.
- If a referral applies without your link, the referral may not be attributed.
- Program terms, eligible industries, and promotional availability may change without notice prior to 2025-09-15.

8. Gold Years Account Referral Program
   ID: doc_checking_accounts_gold_years_account_010
   Score: 14.3974
   Content: ## Refer a friend to Gold Years

Share the benefits of the Gold Years Account with friends and family members who are 62 or older.

### Rewards
- **You receive**: $50 for each successful referral
- **They receive**: $75 as a welcome bonus
- **Annual maximum**: 6 referral bonuses per calendar year

### How to qualify
- The referrer must have maintained checking account status with Rho-Bank for 30 days.
- The person you refer must be eligible for a Gold Years Account (age 62+)
- They must deposit $1,000 within 90 days of account opening

### Referral summary
| Program element | Detail |
|---|---|
| Your bonus | $50 |
| Their bonus | $75 |
| Max referrals/year | 6 |
| Qualifying deposit | $1,000 |
| Deposit deadline | 90 days |
| Customer tenure | 30 days |

### Getting started
1. Find your personalized referral link in your account settings
2. Share it with eligible friends and family
3. Track successful referrals in your rewards dashboard

9. FAQ: Blue Account
   ID: doc_checking_accounts_blue_account_010
   Score: 14.3747
   Content: ## Frequently asked questions

### What does a paper statement cost?
Paper statements are available for $2.50 per month.

### What APY do I earn on my balance?
Your Blue Account earns 0.01% APY on balances.

### Can I set low-balance alerts?
Yes. You can enable alerts at a threshold such as $62 so you are notified when your available balance reaches that level.

### How long do external bank transfers take?
Transfers to another bank typically complete in 2 business days.

### What happens if a deposited check is returned unpaid?
If a deposited check is returned by the issuing bank, a returned deposit fee of $15.00 applies.

### Is there a fee to receive a domestic wire?
Yes. Incoming domestic wires are assessed a fee of $12.50 per wire.

### Does the Blue Account have a referral program?
Yes. When you refer someone to open a Blue Account, you earn $35 for each successful referral. The person you refer receives $30 as a welcome bonus.

### What are the requirements for the referral bonus?
The referred person must deposit at least $500 within 60 days of opening their account. A minimum banking relationship of 30 days is required to participate—this is measured from when you first opened any checking account with us.

### Is there a limit to how many referral bonuses I can earn?
Yes. You can earn up to 5 referral bonuses per calendar year.

10. Dark Green Account Referral Program
   ID: doc_checking_accounts_dark_green_account_010
   Score: 14.2872
   Content: ## Share the Dark Green experience

Refer others to the Dark Green Account and earn rewards when they join.

### Referral rewards
- **Your bonus**: $40 for each qualifying referral
- **Their bonus**: $30 welcome bonus
- **Maximum per year**: 6 referral bonuses

### Qualification criteria
To qualify for the referral bonus:
1. You must satisfy the 45-day minimum as a Rho-Bank checking customer.
2. The person you refer must open a Dark Green Account
3. They must deposit at least $1,000 within 60 days of opening

### Program details
| Aspect | Value |
|---|---|
| Referrer bonus | $40 |
| Referred bonus | $30 |
| Annual cap | 6 referrals |
| Minimum deposit | $1,000 |
| Deposit window | 60 days |
| Tenure required | 45 days |

### Bonus payment
- Bonuses are credited within 5-7 business days after qualification
- Both you and the new member must maintain your accounts in good standing


[Timing: retrieval=2ms, reranking=0ms, total=2ms]

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "id": "skill-22",
  "role": "tool",
  "requestor": "assistant",
  "error": false,
  "turn_idx": 47,
  "timestamp": "2026-11-15T01:54:12.940007"
}
```


</details>

<a id="m048"></a>

### M048 · assistant

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "skill-23",
      "name": "KB_search",
      "arguments": {
        "query": "Sky Blue Account referral program details bonus new member"
      },
      "requestor": "assistant"
    }
  ],
  "is_audio": false,
  "turn_idx": 48,
  "timestamp": "2026-11-15T01:54:12.947618",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 0.006819764996180311,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m049"></a>

### M049 · tool

1. Dark Green Account Referral Program
   ID: doc_checking_accounts_dark_green_account_010
   Score: 21.3338
   Content: ## Share the Dark Green experience

Refer others to the Dark Green Account and earn rewards when they join.

### Referral rewards
- **Your bonus**: $40 for each qualifying referral
- **Their bonus**: $30 welcome bonus
- **Maximum per year**: 6 referral bonuses

### Qualification criteria
To qualify for the referral bonus:
1. You must satisfy the 45-day minimum as a Rho-Bank checking customer.
2. The person you refer must open a Dark Green Account
3. They must deposit at least $1,000 within 60 days of opening

### Program details
| Aspect | Value |
|---|---|
| Referrer bonus | $40 |
| Referred bonus | $30 |
| Annual cap | 6 referrals |
| Minimum deposit | $1,000 |
| Deposit window | 60 days |
| Tenure required | 45 days |

### Bonus payment
- Bonuses are credited within 5-7 business days after qualification
- Both you and the new member must maintain your accounts in good standing

2. True Blue Account: Fee Waivers and Balance Requirements
   ID: doc_business_checking_accounts_true_blue_002
   Score: 21.1080
   Content: ## Waiving your monthly maintenance fee
- You will be charged $75.00 each month unless you meet the waiver threshold.
- The monthly maintenance fee is waived when your balance is at least $50,000 during the statement period.

## Minimum balance requirement vs. fee waiver threshold
- Minimum balance requirement: $25,000 to maintain the account and access premium features.
- Fee waiver threshold: $50,000 to waive the $75.00 monthly maintenance fee.
- Falling below $25,000 may limit access to premium features until your balance is restored.

## Overdrafts and shortfalls
- If your balance goes negative, a per-occurrence overdraft fee of $25.00 may apply.

## How to avoid fees
- Maintain a balance of at least $50,000 to waive the monthly maintenance fee.
- Set internal processes to monitor balances against both $25,000 and $50,000.
- If a shortfall is anticipated, transfer funds promptly to avoid the $25.00 and preserve eligibility for the fee waiver.

## True Blue Referral Program

Refer other high-volume businesses to True Blue and earn significant rewards:

| Benefit | Amount |
| --- | --- |
| Referrer bonus | $350 per referral |
| New member bonus | $250 |
| Maximum referrals per year | 15 |
| Qualifying deposit | $50,000 |
| Deposit window | 120 days |
| Account age requirement | 90 days |

### Referral requirements
- The referred business must deposit $50,000 within 120 days of opening their True Blue account.
- Eligibility is based on how long you've been a Rho-Bank checking customer. The account age threshold is 90 days, calculated from when you opened your oldest checking account.
- Referral bonuses are paid after qualification is confirmed and are subject to the annual limit of 15.

3. Silver Zoom Card: Referral Program - Earn Rewards for Referring Logistics Businesses
   ID: doc_business_credit_cards_silver_zoom_card_011
   Score: 18.3629
   Content: ## How the referral program works
- Earn a referral bonus of $150 for each referred logistics business that is approved and meets the qualifying spend requirement
- Bonuses are capped at 10 per calendar year

## Qualifying activity for your referral
- The referred business must complete purchases totaling $7,500 within 90 days of account opening
- Only one referrer is credited per approved account

## Program timing
- No new referrals are accepted after 2025-10-01

## How to refer
- Share your referral link or submit the referral through your account portal before the referred business applies
- Ensure the referred business uses your link or is otherwise properly attributed during application
- Track referral status within your account until the qualifying spend threshold of $7,500 is met

## Payout details
- Bonuses are typically issued to the referrer after the referred business satisfies the $7,500 requirement within 90 days
- If the referred business returns purchases or does not meet the requirement, no bonus is issued

4. Green Fee-Free Account Referral Program
   ID: doc_checking_accounts_green_fee-free_account_007
   Score: 17.3631
   Content: ## Refer and earn

Help others discover the Green Fee-Free Account and earn rewards for successful referrals.

### Bonus structure
- Your reward: $20 per successful referral
- New member reward: $35 welcome bonus
- Annual limit: 4 referrals per year

### Qualification requirements
For a referral to count as successful:
- The new account holder must deposit at least $300
- This deposit must be made within 60 days of opening their account
- Your Rho-Bank checking relationship must span at least 30 days.

### Quick reference
| Detail | Amount |
|---|---|
| You earn | $20 |
| They earn | $35 |
| Max per year | 4 |
| Required deposit | $300 |
| Deposit deadline | 60 days |
| Referrer eligibility | 30 days |

### How to participate
1. Access your referral link from your account dashboard
2. Share with potential new members
3. Track your referrals and bonuses in the rewards section

5. Beige Account Referral Program
   ID: doc_business_checking_accounts_beige_012
   Score: 17.2087
   Content: ## Enterprise referral program

Refer other enterprise-level businesses to the Beige Account and earn premium referral rewards.

### Premium rewards
- **Your reward**: $500 for each qualifying referral
- **Their reward**: $350 welcome bonus
- **Annual maximum**: 15 referral bonuses per calendar year

### Qualification criteria
To earn a referral bonus:
1. Referrer tenure requirement: 120 days since opening your first checking account with us.
2. The referred enterprise must open a Beige Account
3. They must deposit at least $100,000 within 120 days

### Referral details
| Detail | Amount |
|---|---|
| Referrer bonus | $500 |
| Referred bonus | $350 |
| Maximum per year | 15 |
| Required deposit | $100,000 |
| Deposit window | 120 days |
| Minimum tenure | 120 days |

### How to participate
1. Contact your dedicated relationship manager for referral materials
2. Introduce qualified enterprises to the Beige Account benefits
3. Your relationship manager can facilitate introductions and track referrals
4. Bonuses are credited after all qualification requirements are confirmed

### Enterprise considerations
- Referrals must be for new Beige Account relationships
- Both enterprises must maintain accounts in good standing
- Premium referral bonuses reflect the enterprise-level relationship value

6. Internal: Business Checking Account Promotion - November 2025
   ID: doc_bank_accounts_bank_accounts_(general)_013
   Score: 16.8729
   Content: PROMOTION NOTICE - ACTIVE FROM 11/01/2025 TO 11/30/2025: When recommending business checking accounts to customers, if multiple accounts meet all of the customer's stated requirements, agents should prioritize recommending accounts in the following order: (1) Sky Blue account should be recommended first, as it is currently under promotional priority; (2) Lime Green account should be recommended second, as it is also under promotional priority; (3) All other qualifying accounts may be recommended only if neither Sky Blue nor Lime Green meet the customer's requirements. This promotion is designed to increase adoption of our startup and premium business offerings. Always ensure the recommended account still meets ALL of the customer's stated requirements - do not recommend a promotional account if it does not satisfy the customer's needs.

7. Business Gold Rewards Card: Referral Program - Earn Rewards for Referring Businesses
   ID: doc_business_credit_cards_business_gold_rewards_card_010
   Score: 16.4710
   Content: ## How the Referral Bonus Works
- Earn $200 for each successful referral who is approved and meets the qualifying spend.
- You can earn up to 8 referral bonuses per calendar year.

## Qualifying Spend Requirement
- The referred business must spend $7,500 within 90 from account opening to qualify your bonus.

## Program Timeline
- The referral program accepts new referrals until 2025-09-15. Referrals submitted after this date are not eligible.

## How to Refer
- Generate your unique referral link from your account’s referral center.
- Share the link directly with businesses that consent to receive it.
- Track application status and eligibility in the referral dashboard.

## Payouts
- Once the referred account is approved and completes $7,500 within 90, your $200 is queued for issuance to your account.

## Rules and Best Practices
- Self-referrals are not permitted.
- Share referral invitations only with contacts who have given permission to receive them.
- If a referral applies without your link, the referral may not be attributed.
- Program terms, eligible industries, and promotional availability may change without notice prior to 2025-09-15.

8. Internal: Understanding Credit Card Referral Statuses.
   ID: doc_credit_cards_credit_cards_(general)_001
   Score: 16.1681
   Content: ## Referral status meanings

- COMPLETE — the referred person has successfully opened a new account and met the criteria to get the referral bonus
- IN_PROGRESS — the referred person has successfully opened a new account and is in progress to meet the criteria for the referral bonus
- NO_PROGRESS — the referred person has not applied yet, no progress has been made
- APPLIED — the referred person has sent in the application and is waiting for a decision
- REJECTED — the user has too many referral processes going on
- ERROR — an error has occurred throughout the process

### How to interpret and act
- COMPLETE: The bonus will be granted per the applicable referral program terms.
- IN_PROGRESS: No action required; monitor until criteria are met.
- NO_PROGRESS: You may remind the referrer that the invitee has not started an application.
- APPLIED: Await the application decision; no manual intervention is needed.
- REJECTED: Do not retry immediately; review the user’s existing referral activity before advising next steps.
- ERROR: Retry later or escalate internally if the condition persists.

9. Navy Blue Business Checking: Complete Guide
   ID: doc_business_checking_accounts_navy_blue_001
   Score: 16.1664
   Content: ## Key Account Costs and Limits

- Monthly maintenance fee: $0.00
- Annual Percentage Yield (APY) on balances: 0.5%
- Daily digital transfer limit: $25,000

### What you can expect day to day
- No minimum balance requirement, so you can use the account flexibly.
- Unlimited digital transfers within the daily limit of $25,000.
- Optional overdraft settings are available if you want coverage on eligible transactions.
- E-statements are included at no additional cost.

### Practical tips for managing your account
- Use e-statements to keep records organized and accessible.
- Plan larger transfers with the daily limit of $25,000 in mind; schedule across days if needed.
- Keep an eye on your balance to maximize earnings at 0.5%.

### Quick reference
| Item | Amount |
| --- | --- |
| Monthly maintenance fee | $0.00 |
| APY | 0.5% |
| Daily digital transfer limit | $25,000 |

## Business Referral Program

Grow your network and earn rewards by referring other businesses to Navy Blue:

| Referral Detail | Value |
| --- | --- |
| Your referral bonus | $100 |
| New business welcome bonus | $75 |
| Maximum referrals per year | 10 |
| Required qualifying deposit | $5,000 |
| Deposit must be made within | 90 days |
| Your account age requirement | 60 days |

To qualify: The referred business must open a Navy Blue account and deposit at least $5,000 within 90 days of account opening. Referrer eligibility requires having been a Rho-Bank checking customer for 60 days or more.

10. Internal: Checking Account Referral Program Terms and Restrictions
   ID: doc_bank_accounts_bank_accounts_(general)_047
   Score: 15.4795
   Content: ## Program overview
Each checking account type has its own referral bonus amounts and qualification requirements. This document covers the general terms and restrictions that apply to all checking account referral programs. Before giving any recommendations or information on referral terms, you must check that the user is eligible to submit referrals first, as users who are not eligible to submit referrals while being given recommendations by the agent tend to leave dissatisfactory reviews. 

## Rolling window limit
- You can receive at most 2 referral bonuses in any rolling 9-day window.
- If you attempt to receive more than 2 referrals in a single 9-day period, the third referral (and any subsequent referrals in that window) will be automatically denied.
- This limit applies across all checking account types; referrals from different accounts count toward the same 9-day cap.
- A rolling 9-day window means the count is evaluated based on the exact timestamps of your most recent referral bonuses, not calendar weeks.
- Auto-denied referrals due to the limit cannot be reinstated within the same 9-day window.

## Eligibility restrictions
- The referred person must be a new Rho-Bank customer with no existing checking, savings, or closed accounts within the past 12 months.
- The referrer and referred person cannot be registered at the same address.
- The referred person must be 18 years or older, except for the Light Green Account which allows minors with a guardian.
- For business accounts: The referred business must have a different primary owner than any existing Rho-Bank business account, based on the SSN of the primary authorized signer.

## Referrer tenure policy
- Every referral program requires the referrer to meet a tenure threshold before participating.
- This threshold is calculated from when you first became a Rho-Bank checking customer—specifically, the date your earliest checking account was opened.
- The type of account you currently hold is irrelevant to this calculation. Whether you have a basic or premium product, the tenure measurement remains the same.
- Consequently, holding one account type does not prevent you from referring someone to a different account type, as long as the duration since your first account meets or exceeds the program's stated minimum.

## Bonus conditions
- The qualifying deposit must be new money and cannot be transferred from another Rho-Bank account.
- The qualifying deposit must remain in the account for at least 30 days after the qualifying period ends.
- If the referred account is closed within 90 days of opening, the referral bonus may be reversed (clawback provision).

## Stacking restrictions
- The referral bonus cannot be combined with other new account promotions or sign-up bonuses.
- Only one referral code can be applied per new account.

## Referral status definitions
- COMPLETE — The referred person has successfully opened a new account and met the criteria to receive the referral bonus.
- IN_PROGRESS — The referred person has successfully opened a new account and is working toward meeting the qualifying deposit requirement.
- NO_PROGRESS — The referred person has not applied yet; no progress has been made.
- APPLIED — The referred person has submitted an application and is awaiting a decision.
- REJECTED — The referral has been denied (e.g., rolling window limit exceeded, ineligible referral).
- ERROR — A system error occurred during the referral process.

## Practical guidance
- Track the timing of your last two successful referral bonuses before sending additional referrals.
- If a referral is denied for hitting the rolling window limit, wait until enough time has passed to drop under the cap before attempting another.
- Both accounts must remain in good standing for bonuses to be paid.


[Timing: retrieval=2ms, reranking=0ms, total=2ms]

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "id": "skill-23",
  "role": "tool",
  "requestor": "assistant",
  "error": false,
  "turn_idx": 49,
  "timestamp": "2026-11-15T01:54:12.950292"
}
```


</details>

<a id="m050"></a>

### M050 · assistant

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "skill-24",
      "name": "KB_search",
      "arguments": {
        "query": "Cobalt Blue account at a glance specifications features"
      },
      "requestor": "assistant"
    }
  ],
  "is_audio": false,
  "turn_idx": 50,
  "timestamp": "2026-11-15T01:54:17.108433",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 4.1574041599960765,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m051"></a>

### M051 · tool

1. How to transition a Light Green Account to Blue or Green Account (checking)
   ID: doc_checking_accounts_light_green_account_010
   Score: 15.5883
   Content: ## Determine if the change is automatic
- If Yes is True, your account will convert to an eligible adult checking option automatically at the appropriate time.

## If the change is not automatic
- If Yes is False, initiate a move to Blue or Green Account (checking) by submitting an upgrade request and selecting your preferred account type.

### Before you switch
- Compare features and fees of Blue and Green Account (checking) to choose the best fit.
- Confirm that any scheduled payments or deposits will continue without interruption after the transition.

2. Green Fee-Free Account — summary
   ID: doc_checking_accounts_green_fee-free_account_002
   Score: 13.6211
   Content: ## Quick Summary
- Overdrafts: $0.00
- Monthly maintenance fee: $22.50 (waiver options available; see specifications for details)
- Out-of-network ATM usage (Rho Bank fee): $0.00
- Cashier’s check issuance: $8 per check

## What to Know at a Glance
- You won’t be charged an overdraft fee: $0.00.
- You may avoid the monthly maintenance fee of $22.50 if you meet the waiver criteria.
- Rho Bank does not charge for using non-Rho ATMs: $0.00 (ATM owners may set their own fees).
- Obtain official funds with a cashier’s check for $8.

3. Getting Started with World Blue International Checking
   ID: doc_business_checking_accounts_world_blue_001
   Score: 12.8048
   Content: ## Quick checklist before you begin
- Confirm you can maintain at least $10,000 across currencies to keep the account in good standing
- Be aware of the monthly maintenance fee of $50.00
- Decide which of the up to 35 supported currencies you plan to hold and transact in
- Verify that your intended counterparties and destinations are within the $140 supported regions for sending and receiving payments

## Initial setup steps
- Fund your account so you can meet ongoing balance needs
- Add the currency wallets you will use for operations and settlements
- Set a primary operating currency for reporting and reconciliation
- Configure payee profiles for your frequent counterparties within the supported regions
- Review user access and prepare to assign permissions based on roles and responsibilities

## Key thresholds and limits at a glance

| Item | Value |
|---|---|
| Monthly maintenance fee | $50.00 |
| Minimum balance requirement | $10,000 |
| Supported currencies | 35 |
| Supported regions for payments | $140 |

## First-week best practices
- Keep an operating buffer above $10,000 to avoid service interruptions
- Start with a small set of currency wallets and expand as your payment flows stabilize
- Validate a test payment to a known counterparty in one of the supported regions and confirm posting and reconciliation
- Set alerts and reports aligned to your treasury cadence to monitor balances and activity

## Referring other businesses to World Blue

As a Rho-Bank checking account holder, you can refer other businesses to World Blue. To be eligible to refer:
- You must have maintained checking account status with Rho-Bank for at least 90 days

For a referral to qualify:
- The referred business must open a World Blue account
- They must deposit at least $25,000 within 90 days of account opening


4. True Blue Account: Fee Waivers and Balance Requirements
   ID: doc_business_checking_accounts_true_blue_002
   Score: 12.5980
   Content: ## Waiving your monthly maintenance fee
- You will be charged $75.00 each month unless you meet the waiver threshold.
- The monthly maintenance fee is waived when your balance is at least $50,000 during the statement period.

## Minimum balance requirement vs. fee waiver threshold
- Minimum balance requirement: $25,000 to maintain the account and access premium features.
- Fee waiver threshold: $50,000 to waive the $75.00 monthly maintenance fee.
- Falling below $25,000 may limit access to premium features until your balance is restored.

## Overdrafts and shortfalls
- If your balance goes negative, a per-occurrence overdraft fee of $25.00 may apply.

## How to avoid fees
- Maintain a balance of at least $50,000 to waive the monthly maintenance fee.
- Set internal processes to monitor balances against both $25,000 and $50,000.
- If a shortfall is anticipated, transfer funds promptly to avoid the $25.00 and preserve eligibility for the fee waiver.

## True Blue Referral Program

Refer other high-volume businesses to True Blue and earn significant rewards:

| Benefit | Amount |
| --- | --- |
| Referrer bonus | $350 per referral |
| New member bonus | $250 |
| Maximum referrals per year | 15 |
| Qualifying deposit | $50,000 |
| Deposit window | 120 days |
| Account age requirement | 90 days |

### Referral requirements
- The referred business must deposit $50,000 within 120 days of opening their True Blue account.
- Eligibility is based on how long you've been a Rho-Bank checking customer. The account age threshold is 90 days, calculated from when you opened your oldest checking account.
- Referral bonuses are paid after qualification is confirmed and are subject to the annual limit of 15.

5. Internal: Opening Business Checking Accounts
   ID: doc_bank_accounts_bank_accounts_(general)_003
   Score: 10.8340
   Content: ## Eligibility Requirements

To open a business checking account, ensure all of the following are true:
1. The customer is verified.
2. The customer has at least one existing personal checking account with status OPEN.
3. The customer does not exceed 6 business checking accounts.
4. The customer has no accounts with status CLOSED.
5. The customer's existing checking account has a balance of at least $500.

## Opening Procedure

1. Verify customer identity.
2. Check eligibility requirements listed above.
3. Confirm the customer's desired account_class selection.
   - Business checking account_class options include Navy Blue, Cobalt Blue, True Blue, etc.
4. Use open_bank_account_4821 to open the account.

6. FAQ: Blue Account
   ID: doc_checking_accounts_blue_account_010
   Score: 10.7891
   Content: ## Frequently asked questions

### What does a paper statement cost?
Paper statements are available for $2.50 per month.

### What APY do I earn on my balance?
Your Blue Account earns 0.01% APY on balances.

### Can I set low-balance alerts?
Yes. You can enable alerts at a threshold such as $62 so you are notified when your available balance reaches that level.

### How long do external bank transfers take?
Transfers to another bank typically complete in 2 business days.

### What happens if a deposited check is returned unpaid?
If a deposited check is returned by the issuing bank, a returned deposit fee of $15.00 applies.

### Is there a fee to receive a domestic wire?
Yes. Incoming domestic wires are assessed a fee of $12.50 per wire.

### Does the Blue Account have a referral program?
Yes. When you refer someone to open a Blue Account, you earn $35 for each successful referral. The person you refer receives $30 as a welcome bonus.

### What are the requirements for the referral bonus?
The referred person must deposit at least $500 within 60 days of opening their account. A minimum banking relationship of 30 days is required to participate—this is measured from when you first opened any checking account with us.

### Is there a limit to how many referral bonuses I can earn?
Yes. You can earn up to 5 referral bonuses per calendar year.

7. Troubleshooting: Unexpected Charges on Cobalt Blue
   ID: doc_business_checking_accounts_cobalt_blue_009
   Score: 10.7057
   Content: ## Identify the charge
- Review the exact transaction description on your statement or in your transaction history (e.g., “Monthly Maintenance Fee,” “Wire Transfer – Domestic,” “ATM Fee,” “International ATM Withdrawal Fee,” “Excess Transaction Fee”).
- Note the posting date, amount, and any memo or terminal/location details.
- Compare the posting date to your recent account activity (wires sent, ATM withdrawals, transaction volume, month-end).

## Common Cobalt Blue charges that may appear
| Line item on statement | Why it appears | How to confirm | Amount |
|---|---|---|---|
| Monthly Maintenance Fee | Your account did not meet the balance waiver requirement during the statement period. | Check the Fee Summary on your statement and verify whether your balance met $2,500 for the period. | $20.00 |
| Excess Transaction Fee | You exceeded your monthly free transaction limit. | Count your posted transactions for the statement period and compare to your free allowance; the fee line often notes the number of excess items. | $0.25 per excess transaction |
| Wire Transfer Fee – Domestic | You initiated a domestic wire transfer. | Confirm a wire was submitted on or near the posting date in your transfer history. | $20.00 |
| ATM Fee – Out of Network | You used a non‑Rho ATM in the U.S. | Match the fee date to an ATM withdrawal at a non‑Rho terminal. Note: the ATM owner may also assess a separate surcharge. | $2.00 per ATM transaction |
| International ATM Withdrawal Fee | You withdrew cash at a foreign (international) ATM. | Match the fee date/location to an overseas ATM withdrawal. | 2.5% of the withdrawal amount, minimum $4.00 |

Note: Cobalt Blue does not assess overdraft fees. If you see a charge that appears to be an overdraft fee, review the line’s exact description—it may correspond to one of the fees above. If still unclear, request a review.

## Troubleshooting by charge type

### Monthly Maintenance Fee posted unexpectedly
- Verify whether your account met the waiver balance requirement of $2,500 during the statement period.
- Check if the fee posted at or just after the statement cycle date.
- Compare your balance history for the full period; large debits near period‑end can affect waiver eligibility.
- If you believe you qualified for the waiver, request a fee review and include your statement period dates and balance evidence.

### Excess Transaction Fee you didn’t anticipate
- Add up your posted transactions for the statement period and compare to your plan’s free monthly transaction limit.
- Open the fee detail to see how many items were assessed at $0.25 each.
- If the count appears off, provide a list of the transactions you believe were miscounted when requesting a review.

### Wire Transfer Fee – Domestic you didn’t expect
- Confirm whether a domestic wire was sent on the fee date (or one business day prior).
- Distinguish wires from other transfers by the transaction description (“Wire,” routing via Fedwire, etc.).
- If you did not authorize a wire, report immediately for investigation. Otherwise, the standard fee is $20.00.

### ATM fees: domestic vs. international
- Out‑of‑network (domestic) ATM usage: Expect $2.00 per ATM transaction. This is separate from any surcharge by the ATM owner, which can appear as a separate line item.
- Foreign (international) ATM withdrawals: The fee is 2.5% of the withdrawal amount, with a minimum of $4.00. Example: for a withdrawal, multiply the amount by 2.5%; if that result is less than $4.00, the minimum applies.

## Quick checklist before requesting a review
- Match the fee’s posting date to a specific action (wire, ATM withdrawal, month‑end, spike in transaction volume).
- Capture screenshots of:
  - The fee line item (showing date, amount, and description)
  - Any related transaction (wire confirmation, ATM withdrawal)
  - The relevant statement page (Fee Summary and balance history for the period)
- Briefly explain why the fee appears incorrect (e.g., you met $2,500 during the period, transaction count appears miscalculated, withdrawal was domestic vs. international, etc.).

## Requesting a review or dispute
- Contact us as soon as you notice the charge.
- Include: account name, last 4 digits, statement period, fee date/amount/description, and your supporting screenshots or documents.
- We will investigate and correct any misapplied fees. If additional information is needed (e.g., to verify ATM location or wire authorization), we will follow up.

8. Light Blue Account Referral Program
   ID: doc_checking_accounts_light_blue_account_007
   Score: 10.5221
   Content: ## Earn rewards by referring friends

Share the Light Blue Account with others and earn cash bonuses.

### What you earn
- Referral bonus: $30 for each successful referral
- Maximum referrals: 5 per calendar year

### What they receive
- Welcome bonus: $20 when they open and fund their account

### Requirements

| Requirement | Detail |
|---|---|
| Qualifying deposit | $500 |
| Deposit window | Within 60 days of account opening |
| Referrer tenure | 30 days |

### How it works
1. Share your unique referral link with friends and family
2. They open a Light Blue Account using your link
3. They deposit at least $500 within 60 days
4. You receive $30 and they receive $20

### Eligibility
- To qualify as a referrer, you must have been a Rho-Bank checking account holder for 30 days or longer.
- You can earn up to 5 referral bonuses per calendar year

9. Bronze Saver Account specifications and requirements
   ID: doc_business_savings_accounts_bronze_saver_account_002
   Score: 10.2339
   Content: ## Specifications
| Item | Details |
| --- | --- |
| Minimum opening deposit | $0 |
| Interest compounding frequency | daily |
| Linked Rho-Bank business checking required | Yes |

## Requirements guidance
- Ensure a linked Rho-Bank business checking account remains active if Yes is required for your setup.
- Confirm your compounding preference is set to daily in your account details.
- Verify the initial funding meets or exceeds $0.

10. Internal: Business Checking Account Promotion - November 2025
   ID: doc_bank_accounts_bank_accounts_(general)_013
   Score: 10.0048
   Content: PROMOTION NOTICE - ACTIVE FROM 11/01/2025 TO 11/30/2025: When recommending business checking accounts to customers, if multiple accounts meet all of the customer's stated requirements, agents should prioritize recommending accounts in the following order: (1) Sky Blue account should be recommended first, as it is currently under promotional priority; (2) Lime Green account should be recommended second, as it is also under promotional priority; (3) All other qualifying accounts may be recommended only if neither Sky Blue nor Lime Green meet the customer's requirements. This promotion is designed to increase adoption of our startup and premium business offerings. Always ensure the recommended account still meets ALL of the customer's stated requirements - do not recommend a promotional account if it does not satisfy the customer's needs.


[Timing: retrieval=2ms, reranking=0ms, total=2ms]

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "id": "skill-24",
  "role": "tool",
  "requestor": "assistant",
  "error": false,
  "turn_idx": 51,
  "timestamp": "2026-11-15T01:54:17.110858"
}
```


</details>

<a id="m052"></a>

### M052 · assistant

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "skill-25",
      "name": "KB_search",
      "arguments": {
        "query": "referral link tool checking account customer run get_referral_link"
      },
      "requestor": "assistant"
    }
  ],
  "is_audio": false,
  "turn_idx": 52,
  "timestamp": "2026-11-15T01:54:17.119013",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 0.007423264003591612,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m053"></a>

### M053 · tool

1. Generating a Credit Card Referral Link (Internal)
   ID: doc_credit_cards_credit_cards_(general)_009
   Score: 23.0085
   Content: ## Pre-check before providing the referral tool
- Search the knowledge base to confirm the specific card has a documented referral program.
- Verify the customer’s understanding of referral terms. If the customer cites terms that do not match any documented program, clarify the discrepancy.
- If no referral program is documented for the requested card, or if the user’s claimed terms are incorrect, or if there is reason to believe the referral will be automatically rejected, explain why and do not provide a referral link tool. Do not transfer to a human in these cases.

## How the user generates their referral link
- Provide the customer with this tool and instruct them to run it themselves:
  - `get_referral_link(user_id: str, card_name: str)`
- Tell the customer to pass their own user_id and the exact card name (for example, 'Gold Rewards Card').
- When the tool is called successfully, a referral record is created with status 'NO_PROGRESS'. The referred person can then use the generated link to apply.

## Important reminders
- Weekly limit: Customers can receive at most 2 referral bonuses in any rolling 7-day window; the third and subsequent referrals in that window are automatically denied.
- Agents must not generate the link on the customer’s behalf.
- Reiterate the correct referral terms as documented to prevent confusion and complaints.

2. Paying Off Credit Card Balance from Checking Account (Internal)
   ID: doc_credit_cards_credit_card_account_logistics_009
   Score: 15.3510
   Content: ## Purpose

When a customer needs to pay off their credit card balance using funds from their Rho-Bank checking account, you can process the payment directly.

## Prerequisites

1. Verify the customer's identity using standard procedures.
2. Confirm the customer has a Rho-Bank checking account with sufficient funds to cover the payment amount.
3. Look up both the checking account and credit card account to obtain account IDs and verify balances.

## Process

1. Verify the customer's identity.
2. Look up the customer's checking account to confirm sufficient funds.
3. Look up the customer's credit card account to confirm the outstanding balance.
4. Confirm the payment amount with the customer and obtain authorization to transfer.
5. Unlock the pay_credit_card_from_checking_9182 tool using unlock_discoverable_agent_tool.
6. Call the tool using call_discoverable_agent_tool with the required arguments listed below.

## Tool Arguments for pay_credit_card_from_checking_9182

- user_id (string, required): The customer's unique identifier in the system.
- checking_account_id (string, required): The ID of the Rho-Bank checking account to debit.
- credit_card_account_id (string, required): The ID of the credit card account to credit.
- amount (float, required): The payment amount in dollars. Must be positive and cannot exceed the checking account balance or the credit card outstanding balance.

The tool will debit the specified amount from the checking account and reduce the credit card balance by the same amount. A confirmation will include the new balances for both accounts.

## Instructions for Passing the Tool

- Use unlock_discoverable_agent_tool to enable pay_credit_card_from_checking_9182 for the session.
- Then pass the arguments via call_discoverable_agent_tool exactly as listed above, ensuring the account IDs and user_id match the authenticated customer and the amount is authorized.

3. Gold Years Account Referral Program
   ID: doc_checking_accounts_gold_years_account_010
   Score: 15.2555
   Content: ## Refer a friend to Gold Years

Share the benefits of the Gold Years Account with friends and family members who are 62 or older.

### Rewards
- **You receive**: $50 for each successful referral
- **They receive**: $75 as a welcome bonus
- **Annual maximum**: 6 referral bonuses per calendar year

### How to qualify
- The referrer must have maintained checking account status with Rho-Bank for 30 days.
- The person you refer must be eligible for a Gold Years Account (age 62+)
- They must deposit $1,000 within 90 days of account opening

### Referral summary
| Program element | Detail |
|---|---|
| Your bonus | $50 |
| Their bonus | $75 |
| Max referrals/year | 6 |
| Qualifying deposit | $1,000 |
| Deposit deadline | 90 days |
| Customer tenure | 30 days |

### Getting started
1. Find your personalized referral link in your account settings
2. Share it with eligible friends and family
3. Track successful referrals in your rewards dashboard

4. FAQ: Troubleshooting
   ID: doc_checking_accounts_checking_accounts_(general)_002
   Score: 15.1095
   Content: ## Quick checks to resolve common issues
- Ensure the customer is using the latest version of the mobile app or a supported web browser.
- Confirm the account is active and the customer is signed in with the correct profile.
- Verify that connectivity is stable and ask the customer to try a different network if possible.
- If the user experiences any issues with the website, they should try refreshing their cache using the `refresh_cache` tool.

## User-callable tool: Refresh cached site data
Provide the following tool directly to the user and instruct them to run it. Do not execute it on their behalf.
- Tool signature: `refresh_cache()`
- What to tell the user: “Please run the `refresh_cache()` tool to clear your cached site data and reload the latest version of the website.”
- Why this replaces manual steps: Instead of walking through browser settings, provide the exact tool name (and parameters, if any) so the user can perform the refresh immediately.

## Scenario-based guidance
- Balance not updating after a deposit: Ask the user to sign out and back in after running `refresh_cache()`. Then recheck the account activity screen.
- Transaction missing or pending: Review pending activity; some card authorizations and merchant adjustments take time to finalize.
- Transfers appear stuck: Confirm destination account details and any external bank maintenance notices; recheck status after a refreshed session.
- Sign-in problems: Verify correct username, recent password changes, and that the customer is not using a VPN that could trigger additional security checks.

## When to escalate
- The issue persists across devices and networks after the user runs `refresh_cache()` and signs back in.
- The customer reports specific error codes or repeated failures initiating payments, deposits, or transfers.
- Security concerns (e.g., suspected unauthorized access) or account access lockouts.

5. Light Blue Account Referral Program
   ID: doc_checking_accounts_light_blue_account_007
   Score: 15.0307
   Content: ## Earn rewards by referring friends

Share the Light Blue Account with others and earn cash bonuses.

### What you earn
- Referral bonus: $30 for each successful referral
- Maximum referrals: 5 per calendar year

### What they receive
- Welcome bonus: $20 when they open and fund their account

### Requirements

| Requirement | Detail |
|---|---|
| Qualifying deposit | $500 |
| Deposit window | Within 60 days of account opening |
| Referrer tenure | 30 days |

### How it works
1. Share your unique referral link with friends and family
2. They open a Light Blue Account using your link
3. They deposit at least $500 within 60 days
4. You receive $30 and they receive $20

### Eligibility
- To qualify as a referrer, you must have been a Rho-Bank checking account holder for 30 days or longer.
- You can earn up to 5 referral bonuses per calendar year

6. Internal: Opening Business Savings Accounts
   ID: doc_bank_accounts_bank_accounts_(general)_004
   Score: 14.6704
   Content: ## Description

Procedure for opening business savings accounts. Eligibility requirements: 1) Customer must be verified, 2) Customer must already have at least one business checking account with status OPEN, 3) Customer cannot have more than 4 business savings accounts, 4) Customer must not have any accounts with negative balances, 5) Existing business checking account must have been open for at least 30 days, 6) Existing business checking account must have a balance of at least $2,500. Steps: 1) Verify customer identity, 2) Check eligibility requirements, 3) Confirm account selection with customer (business savings account_class options include Bronze Saver Account, Silver Saver Account, etc.), 4) Use open_bank_account_4821 to open the account, 5) Ask the customer if they would like you to transfer the opening deposit from their business checking account now. If yes, use transfer_funds_between_bank_accounts_7291 to transfer the required amount. If no, inform them they have 30 days to fund the account (via internal transfer or external deposit) or the account will be closed.

## Eligibility Requirements

Confirm all of the following before proceeding:
- Customer identity is verified.
- Customer has at least one business checking account with status OPEN.
- Customer has fewer than 4 existing business savings accounts.
- Customer has no accounts with negative balances.
- At least one existing business checking account has been open for at least 30 days.
- That business checking account has a current balance of at least $2,500.

Notes:
- Use the qualifying OPEN business checking account that meets both the tenure and balance thresholds as the source for the optional opening deposit transfer.

## Step-by-Step Procedure

1) Verify customer identity.
2) Check eligibility requirements (see list above).
3) Confirm account selection with the customer:
   - Ask for the desired business savings account_class (e.g., Bronze Saver Account, Silver Saver Account, etc.).
   - Ensure you capture the exact official account_class name ending with “Account.”
4) Open the new business savings account using the agent tool (see Tool Instructions below).
5) Funding the opening deposit:
   - Ask the customer if they want you to transfer the opening deposit now from their eligible business checking account.
   - If yes: initiate the internal transfer using the agent tool (see Tool Instructions below).
   - If no: inform the customer they have 30 days to fund the account via internal transfer or external deposit; otherwise, the account will be closed.

## Agent Tool Instructions

The AGENT calls these tools directly to perform actions on behalf of the customer. Do not expose tool details to the customer.

### Tool: open_bank_account_4821

- Signature:
  - open_bank_account_4821(user_id, account_type, account_class)
- When to call:
  - After eligibility is confirmed and the customer has selected the desired business savings account_class.
- How to call:
  - Set account_type to 'savings'.
  - Set account_class to the exact official name provided by the customer (e.g., 'Bronze Saver Account').
- Expected outcome:
  - Returns a new savings account record (capture the new account_id for subsequent actions).

### Tool: transfer_funds_between_bank_accounts_7291

- Signature:
  - transfer_funds_between_bank_accounts_7291(source_account_id, destination_account_id, amount)
- When to call:
  - Only if the customer authorizes transferring the opening deposit now.
- How to call:
  - source_account_id: the qualifying OPEN business checking account that meets the 30-day tenure and $2,500 balance requirements.
  - destination_account_id: the newly opened business savings account_id.
  - amount: the required opening deposit amount confirmed with the customer.
- If the transfer fails (e.g., insufficient funds):
  - Inform the customer and remind them they have 30 days to fund the account via internal transfer or external deposit, or the account will be closed.

## Checklist Before Opening

- Customer identity verified.
- OPEN business checking account identified and qualified (≥ 30 days open and ≥ $2,500 balance).
- Savings account count confirmed is < 4.
- No negative balances across any accounts.
- Customer-confirmed account_class captured exactly.

## Post-Opening Actions

- If the customer funds now: complete the transfer and confirm success.
- If the customer defers funding: clearly communicate the 30-day deadline and acceptable methods (internal transfer or external deposit), and note that the account will be closed if not funded within that timeframe.

7. Submitting a Cash Back Dispute (Internal)
   ID: doc_credit_cards_credit_cards_(general)_003
   Score: 14.0575
   Content: ## When to use this
Use this process when a customer believes there is a discrepancy between the cash back they received for a particular transaction and the cash back they should have received. This process applies to all credit card transactions.

## How to submit the dispute
Instead of a step-by-step workflow, instruct the customer to use the tool directly:

- Tool to provide to the user: `submit_cash_back_dispute_0589(user_id: str, transaction_id: str)`
- Tell the customer to run the tool with their own user_id and the specific transaction_id for the purchase in question.

## Agent notes
- Confirm the customer has the correct transaction_id before they submit.
- Do not collect sensitive card details; the tool uses the identifiers provided by the user.
- Advise the customer that supporting context (e.g., category or promotion expectations) may be requested later during review, but the submission itself is initiated with the tool above.

8. Internal: Retrieving Debit Card Information
   ID: doc_bank_accounts_bank_accounts_(general)_028
   Score: 13.5423
   Content: Tool for retrieving debit card information for a customer's checking account. Use get_debit_cards_by_account_id_7823 to look up all debit cards associated with a specific checking account.

## Tool Usage

get_debit_cards_by_account_id_7823(account_id) - account_id is the checking account ID to retrieve debit cards for.

## Debit Card Fields Returned

- card_id: Unique identifier for the debit card
- account_id: The checking account ID the card is linked to
- user_id: The user ID of the cardholder
- card_number_last_4: Last 4 digits of the card number
- status: Current status of the card (ACTIVE, PENDING, FROZEN, CLOSED)
- issue_reason: Why the card was issued (new_account, first_card, lost, stolen, fraud, expired, damaged, upgrade, bank_reissue)
- expiration_date: Card expiration date (MM/YY format)
- date_issued: Date the card was issued
- card_design: Design type (CLASSIC, PREMIUM, CUSTOM)
- daily_purchase_limit: Maximum daily purchase amount
- daily_atm_limit: Maximum daily ATM withdrawal amount

## Common Use Cases

1. Before ordering a new debit card: Check if customer already has an active or pending card for the account
2. Before activating a card: Look up the issue_reason to determine which activation tool to use
3. Before freezing/unfreezing: Verify the card exists and check its current status
4. Before closing a card: Confirm the card_id and current status
5. Customer inquiries: Look up card details when customer asks about their debit card

## Important Notes

- This tool only returns debit cards for checking accounts (savings accounts do not have debit cards)
- Multiple cards may be returned if the account has card history (e.g., old closed cards plus current active card)
- For privacy, full card numbers are never returned - only the last 4 digits
- If no cards exist for the account, an empty list is returned

9. Internal: Applying Credits and Rebates to Checking Accounts
   ID: doc_bank_accounts_bank_accounts_(general)_017
   Score: 13.3876
   Content: ## Overview

This document describes the policy and procedure for agents to apply credits to customer checking accounts. Credits may only be applied to checking accounts (not savings accounts or other account types). The apply_checking_account_credit_5829 tool is used to add a credit transaction to a checking account.

## Eligible Circumstances for Applying Credits

Agents are authorized to apply credits to checking accounts ONLY in the following circumstances:

### 1. Missing Rebates

If a rebate that should have been applied to the customer's account has not yet been applied, and the customer meets all eligibility requirements for that rebate, the agent may apply the credit. Before applying:
- Verify the customer is eligible for the rebate based on documented rebate policies
- Confirm the rebate has not already been applied by checking the account's transaction history
- Ensure the rebate amount matches what is specified in the applicable rebate policy

### 2. Fee mischarges

If any fees on the customer's account do not match the correct amounts per the documented fee schedule, the agent must identify all fee discrepancies and apply a credit for the net correction. Before applying:
- Review the account terms and documented fee structures to identify all fees that differ from what should have been charged
- Check the transaction history to confirm each fee discrepancy
- Ensure the credit amount reflects the net correction across all identified fee discrepancies

## Credit Types

When applying a credit, use the appropriate credit_type:
- `rebate_credit`: For rebates that should have been applied but were missing
- `fee_refund`: For refunding fees that were incorrectly charged

## Procedure

1. Verify the customer's identity and account ownership
2. Confirm the account is a checking account (credits cannot be applied to savings or other account types)
3. Verify the customer meets one of the eligible circumstances listed above
4. Calculate the correct credit amount based on the rebate policy or fee that was overcharged
5. Use the apply_checking_account_credit_5829 tool to apply the credit
6. Inform the customer of the applied credit and new account balance

## Agent Tool Usage (Internal Only)

- Tool: apply_checking_account_credit_5829(account_id, amount, credit_type)
  - When to call: After confirming the customer meets one of the eligible circumstances above
  - How to set parameters:
    - account_id: The checking account ID to credit
    - amount: The positive dollar amount to credit (must be greater than 0)
    - credit_type: Must be one of 'rebate_credit' or 'fee_refund'
  - Expected outcome: Adds a credit transaction to the checking account and updates the account balance

The apply_checking_account_credit_5829 tool may only be called ONCE per checking account per customer interaction. After a credit is applied to a checking account, the system enforces a 14-day cooldown period before another credit can be applied to that same account. Because only one credit call is allowed per account, if multiple corrections are needed for the same account (e.g., both fee refunds and missing rebates), combine them into a single credit with the total amount and use the credit_type that applies to the majority of the corrections.

## Important Restrictions

- Credits may ONLY be applied to checking accounts. Savings accounts and other account types are not eligible.
- Credits may only be applied for the two circumstances listed above. Do not apply credits for any other reason without supervisor approval.
- Always document the reason for the credit by selecting the appropriate credit_type. 
- The credit amount must match the exact rebate or fee amount - do not round or estimate.

10. Business Bronze Rewards Card: Referral Program - Earn Rewards for Referring Businesses
   ID: doc_business_credit_cards_business_bronze_rewards_card_011
   Score: 13.3686
   Content: ## What You Can Earn
- Receive $75 for each successful referral.
- You can earn up to 7 referral bonuses per calendar year.

## What Makes a Referral Successful
- The referred business must be approved for the card.
- The referred business must complete at least $1,750 in net purchases within 90 days of account opening.

## How to Refer
1. Share your referral link or code with another business.
2. Ensure they apply using your link or enter your code during their application.
3. You will be notified when the referral is approved and has met the $1,750 requirement within 90 days.

## Tracking Your Bonuses
- Monitor referral status, qualifying spend progress, and paid bonuses in your account dashboard.
- If a referred account is closed or reversed, any unpaid referral bonus may be canceled.

## Best Practices
- Encourage referrals to complete their initial purchases early to meet the $1,750 requirement within 90 days.
- Remind referrals to use your link or code so your bonus is tracked correctly.


[Timing: retrieval=2ms, reranking=0ms, total=2ms]

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "id": "skill-25",
  "role": "tool",
  "requestor": "assistant",
  "error": false,
  "turn_idx": 53,
  "timestamp": "2026-11-15T01:54:17.121748"
}
```


</details>

<a id="m054"></a>

### M054 · assistant

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "skill-26",
      "name": "KB_search",
      "arguments": {
        "query": "FAQ Cobalt Blue referral bonus how much earn per referral"
      },
      "requestor": "assistant"
    }
  ],
  "is_audio": false,
  "turn_idx": 54,
  "timestamp": "2026-11-15T01:54:22.224609",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 5.101984328997787,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m055"></a>

### M055 · tool

1. Light Blue Account Referral Program
   ID: doc_checking_accounts_light_blue_account_007
   Score: 20.7743
   Content: ## Earn rewards by referring friends

Share the Light Blue Account with others and earn cash bonuses.

### What you earn
- Referral bonus: $30 for each successful referral
- Maximum referrals: 5 per calendar year

### What they receive
- Welcome bonus: $20 when they open and fund their account

### Requirements

| Requirement | Detail |
|---|---|
| Qualifying deposit | $500 |
| Deposit window | Within 60 days of account opening |
| Referrer tenure | 30 days |

### How it works
1. Share your unique referral link with friends and family
2. They open a Light Blue Account using your link
3. They deposit at least $500 within 60 days
4. You receive $30 and they receive $20

### Eligibility
- To qualify as a referrer, you must have been a Rho-Bank checking account holder for 30 days or longer.
- You can earn up to 5 referral bonuses per calendar year

2. True Blue Account: Fee Waivers and Balance Requirements
   ID: doc_business_checking_accounts_true_blue_002
   Score: 19.6926
   Content: ## Waiving your monthly maintenance fee
- You will be charged $75.00 each month unless you meet the waiver threshold.
- The monthly maintenance fee is waived when your balance is at least $50,000 during the statement period.

## Minimum balance requirement vs. fee waiver threshold
- Minimum balance requirement: $25,000 to maintain the account and access premium features.
- Fee waiver threshold: $50,000 to waive the $75.00 monthly maintenance fee.
- Falling below $25,000 may limit access to premium features until your balance is restored.

## Overdrafts and shortfalls
- If your balance goes negative, a per-occurrence overdraft fee of $25.00 may apply.

## How to avoid fees
- Maintain a balance of at least $50,000 to waive the monthly maintenance fee.
- Set internal processes to monitor balances against both $25,000 and $50,000.
- If a shortfall is anticipated, transfer funds promptly to avoid the $25.00 and preserve eligibility for the fee waiver.

## True Blue Referral Program

Refer other high-volume businesses to True Blue and earn significant rewards:

| Benefit | Amount |
| --- | --- |
| Referrer bonus | $350 per referral |
| New member bonus | $250 |
| Maximum referrals per year | 15 |
| Qualifying deposit | $50,000 |
| Deposit window | 120 days |
| Account age requirement | 90 days |

### Referral requirements
- The referred business must deposit $50,000 within 120 days of opening their True Blue account.
- Eligibility is based on how long you've been a Rho-Bank checking customer. The account age threshold is 90 days, calculated from when you opened your oldest checking account.
- Referral bonuses are paid after qualification is confirmed and are subject to the annual limit of 15.

3. FAQ: Blue Account
   ID: doc_checking_accounts_blue_account_010
   Score: 19.6080
   Content: ## Frequently asked questions

### What does a paper statement cost?
Paper statements are available for $2.50 per month.

### What APY do I earn on my balance?
Your Blue Account earns 0.01% APY on balances.

### Can I set low-balance alerts?
Yes. You can enable alerts at a threshold such as $62 so you are notified when your available balance reaches that level.

### How long do external bank transfers take?
Transfers to another bank typically complete in 2 business days.

### What happens if a deposited check is returned unpaid?
If a deposited check is returned by the issuing bank, a returned deposit fee of $15.00 applies.

### Is there a fee to receive a domestic wire?
Yes. Incoming domestic wires are assessed a fee of $12.50 per wire.

### Does the Blue Account have a referral program?
Yes. When you refer someone to open a Blue Account, you earn $35 for each successful referral. The person you refer receives $30 as a welcome bonus.

### What are the requirements for the referral bonus?
The referred person must deposit at least $500 within 60 days of opening their account. A minimum banking relationship of 30 days is required to participate—this is measured from when you first opened any checking account with us.

### Is there a limit to how many referral bonuses I can earn?
Yes. You can earn up to 5 referral bonuses per calendar year.

4. Business Silver Rewards Card: Referral Program - Earn Rewards for Referring Businesses
   ID: doc_business_credit_cards_business_silver_rewards_card_013
   Score: 19.3898
   Content: ## What you can earn
- Earn $100 for each successful referral that is approved and meets the qualifying spend requirement
- You can earn up to 10 referral bonuses per calendar year

## Qualifying spend requirement
- The referred business must spend at least $3,000 within 90 days of account opening for you to receive the bonus

## How to refer
- Share a referral through the official referral channel so applications are tracked correctly
- Ensure the referred business uses your referral details when applying

## Tracking and payout
- After the referred business is approved and completes the qualifying spend, your $100 bonus will be processed according to program rules
- If a referral does not appear, contact support with the referred business name and application date so it can be investigated

5. Beige Account Referral Program
   ID: doc_business_checking_accounts_beige_012
   Score: 18.9615
   Content: ## Enterprise referral program

Refer other enterprise-level businesses to the Beige Account and earn premium referral rewards.

### Premium rewards
- **Your reward**: $500 for each qualifying referral
- **Their reward**: $350 welcome bonus
- **Annual maximum**: 15 referral bonuses per calendar year

### Qualification criteria
To earn a referral bonus:
1. Referrer tenure requirement: 120 days since opening your first checking account with us.
2. The referred enterprise must open a Beige Account
3. They must deposit at least $100,000 within 120 days

### Referral details
| Detail | Amount |
|---|---|
| Referrer bonus | $500 |
| Referred bonus | $350 |
| Maximum per year | 15 |
| Required deposit | $100,000 |
| Deposit window | 120 days |
| Minimum tenure | 120 days |

### How to participate
1. Contact your dedicated relationship manager for referral materials
2. Introduce qualified enterprises to the Beige Account benefits
3. Your relationship manager can facilitate introductions and track referrals
4. Bonuses are credited after all qualification requirements are confirmed

### Enterprise considerations
- Referrals must be for new Beige Account relationships
- Both enterprises must maintain accounts in good standing
- Premium referral bonuses reflect the enterprise-level relationship value

6. Business Platinum Rewards Card: Referral Program - Earn Rewards for Referring Businesses
   ID: doc_business_credit_cards_business_platinum_rewards_card_012
   Score: 18.5965
   Content: ## How the Referral Bonus Works
- Share your referral through the designated channel. When the referred business is approved and completes qualifying spend of $15,000 within 135 days from account opening, you earn a bonus of $300.

## Annual Limits
- You can earn up to 11 referral bonuses per calendar year.

## Qualification Tips
- Encourage the referred business to use the card for eligible purchases promptly after activation to meet $15,000 within the allowed period.
- Ensure the referral is submitted before the application so it is properly attributed.

## Payout and Compliance
- Bonuses are credited to your account after verification that approval and qualifying spend requirements have been met.
- Referrals should comply with applicable marketing and solicitation rules; only share referral information with contacts who have consented to receive it.

7. Earning Interest on Your World Blue Balance
   ID: doc_business_checking_accounts_world_blue_007
   Score: 18.3299
   Content: ## Rate and compounding
- Your USD balance earns an Annual Percentage Yield of 1.0%
- Interest is compounded daily

## How interest is applied
- Interest accrues on eligible USD funds held in the account and is credited in accordance with your statement cycle
- If you move funds between currencies, only USD balances accrue interest at 1.0%

## Monitoring your earnings
- Track accrued and credited interest in your account activity and statements
- Export transaction data to reconcile interest income in your general ledger

## Tips for maximizing earned interest
- Keep operational reserves in USD when appropriate so they benefit from compounding daily
- Align conversion and payout timing with your cash needs so idle USD balances remain interest-earning as long as practicable

## Referral bonuses for World Blue members

In addition to interest earnings, you can earn rewards by referring other international businesses to World Blue:

- **Your bonus**: $300 for each successful referral
- **Their bonus**: $200 welcome bonus for the new business
- **Annual limit**: 12 referral bonuses per calendar year

Referral bonuses are typically credited within 7-10 business days of qualification. Both accounts must remain in good standing for bonuses to be paid.


8. Silver Rewards Card: Referral Program - Earn Rewards for Referring Friends
   ID: doc_credit_cards_silver_rewards_card_011
   Score: 18.1478
   Content: ## What You Earn
- Receive 75 for each successful referral
- You can earn up to 7 referral bonuses per calendar year

## What Your Referral Must Do
- The referred person must be approved and spend at least $750 within 60 days of account opening

## How to Refer
1. Share your referral link or code with friends and colleagues
2. Ensure they apply using your link or code so the referral is tracked
3. You’ll be notified when the referral meets the qualifying spend requirement

## Payout Timing
- Your bonus typically posts within one to two billing cycles after the referred account meets the $750 requirement

## Program Tips
- Remind your referral to activate their card promptly and add recurring bills to help them meet $750 within 60 days
- Track your annual count to stay within the 7 limit

9. EcoCard: Referral Program - Earn Rewards for Referring Friends
   ID: doc_credit_cards_ecocard_011
   Score: 18.1478
   Content: ## What You Earn
- Receive 50 for each successful referral
- You can earn up to 7 referral bonuses per calendar year

## What Your Referral Must Do
- The referred person must be approved and spend at least $500 within 60 days of account opening

## How to Refer
1. Share your referral link or code with friends and family
2. Ensure they apply using your link or code so the referral is tracked
3. You'll be notified when the referral meets the qualifying spend requirement

## Payout Timing
- Your bonus typically posts within one to two billing cycles after the referred account meets the $500 requirement

## Program Tips
- Remind your referral to activate their card promptly and add recurring bills to help them meet $500 within 60 days
- Track your annual count to stay within the 7 limit

10. Business Bronze Rewards Card: Referral Program - Earn Rewards for Referring Businesses
   ID: doc_business_credit_cards_business_bronze_rewards_card_011
   Score: 18.1022
   Content: ## What You Can Earn
- Receive $75 for each successful referral.
- You can earn up to 7 referral bonuses per calendar year.

## What Makes a Referral Successful
- The referred business must be approved for the card.
- The referred business must complete at least $1,750 in net purchases within 90 days of account opening.

## How to Refer
1. Share your referral link or code with another business.
2. Ensure they apply using your link or enter your code during their application.
3. You will be notified when the referral is approved and has met the $1,750 requirement within 90 days.

## Tracking Your Bonuses
- Monitor referral status, qualifying spend progress, and paid bonuses in your account dashboard.
- If a referred account is closed or reversed, any unpaid referral bonus may be canceled.

## Best Practices
- Encourage referrals to complete their initial purchases early to meet the $1,750 requirement within 90 days.
- Remind referrals to use your link or code so your bonus is tracked correctly.


[Timing: retrieval=2ms, reranking=0ms, total=2ms]

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "id": "skill-26",
  "role": "tool",
  "requestor": "assistant",
  "error": false,
  "turn_idx": 55,
  "timestamp": "2026-11-15T01:54:22.226965"
}
```


</details>

<a id="m056"></a>

### M056 · assistant

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "skill-27",
      "name": "KB_search",
      "arguments": {
        "query": "how to refer a business to open checking account referral link dashboard or tool"
      },
      "requestor": "assistant"
    }
  ],
  "is_audio": false,
  "turn_idx": 56,
  "timestamp": "2026-11-15T01:54:22.234064",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 0.006675525990431197,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m057"></a>

### M057 · tool

1. Gold Years Account Referral Program
   ID: doc_checking_accounts_gold_years_account_010
   Score: 29.0174
   Content: ## Refer a friend to Gold Years

Share the benefits of the Gold Years Account with friends and family members who are 62 or older.

### Rewards
- **You receive**: $50 for each successful referral
- **They receive**: $75 as a welcome bonus
- **Annual maximum**: 6 referral bonuses per calendar year

### How to qualify
- The referrer must have maintained checking account status with Rho-Bank for 30 days.
- The person you refer must be eligible for a Gold Years Account (age 62+)
- They must deposit $1,000 within 90 days of account opening

### Referral summary
| Program element | Detail |
|---|---|
| Your bonus | $50 |
| Their bonus | $75 |
| Max referrals/year | 6 |
| Qualifying deposit | $1,000 |
| Deposit deadline | 90 days |
| Customer tenure | 30 days |

### Getting started
1. Find your personalized referral link in your account settings
2. Share it with eligible friends and family
3. Track successful referrals in your rewards dashboard

2. Business Bronze Rewards Card: Referral Program - Earn Rewards for Referring Businesses
   ID: doc_business_credit_cards_business_bronze_rewards_card_011
   Score: 28.6521
   Content: ## What You Can Earn
- Receive $75 for each successful referral.
- You can earn up to 7 referral bonuses per calendar year.

## What Makes a Referral Successful
- The referred business must be approved for the card.
- The referred business must complete at least $1,750 in net purchases within 90 days of account opening.

## How to Refer
1. Share your referral link or code with another business.
2. Ensure they apply using your link or enter your code during their application.
3. You will be notified when the referral is approved and has met the $1,750 requirement within 90 days.

## Tracking Your Bonuses
- Monitor referral status, qualifying spend progress, and paid bonuses in your account dashboard.
- If a referred account is closed or reversed, any unpaid referral bonus may be canceled.

## Best Practices
- Encourage referrals to complete their initial purchases early to meet the $1,750 requirement within 90 days.
- Remind referrals to use your link or code so your bonus is tracked correctly.

3. FAQ: Checking Account Referrals
   ID: doc_bank_accounts_bank_accounts_(general)_048
   Score: 28.0162
   Content: ## Frequently asked questions about checking account referrals

### How many people can I refer at once?
You can have multiple referrals in progress, but you can only receive a maximum of 2 referral bonuses in any rolling 9-day window. If you exceed this limit, additional referrals will be automatically denied until enough time passes.

### Can I refer someone who used to have a Rho-Bank account?
No. The referred person must be a new Rho-Bank customer with no existing or closed accounts within the past 12 months. Former customers must wait 12 months after their last account closure before being eligible as a referral.

### Can I refer someone who lives at the same address as me?
No. The referrer and referred person cannot be registered at the same address. This restriction helps prevent abuse of the referral program.

### What counts as a qualifying deposit?
The qualifying deposit must be new money brought into Rho-Bank. Transfers from another Rho-Bank account do not count. The deposit can come from an external bank transfer, direct deposit, mobile check deposit, or cash/check deposit at a branch.

### What happens if the person I referred closes their account early?
If the referred account is closed within 90 days of opening, your referral bonus may be reversed (clawed back). Both accounts must remain in good standing for bonuses to be retained.

### Can I combine the referral bonus with other promotions?
No. The referral bonus cannot be combined with other new account promotions or sign-up bonuses. Only one promotional offer can be applied per new account.

### What do the referral statuses mean?
- **COMPLETE**: The referral was successful and bonuses will be paid.
- **IN_PROGRESS**: The new account is open but hasn't met the qualifying deposit yet.
- **NO_PROGRESS**: The referred person hasn't started an application.
- **APPLIED**: An application has been submitted and is being reviewed.
- **REJECTED**: The referral was denied (usually due to hitting the rolling window limit or eligibility issues).
- **ERROR**: A system error occurred; try again later or contact support.

### Why was my referral rejected?
Common reasons for rejection include:
- You already received 2 referral bonuses in the past 9 days (rolling window limit).
- The referred person already has or recently had a Rho-Bank account.
- You and the referred person are registered at the same address.
- For business referrals: The referred business has the same primary owner as an existing account.

### How long do I have to wait after a rejection to refer again?
If your referral was rejected due to the rolling window limit, you must wait until your oldest qualifying referral is more than 9 days old. The limit is based on a rolling window, so you become eligible again as older referrals age out.

### Can I refer someone for a business checking account?
Yes, but the referred business must have a different primary owner (based on SSN of the primary authorized signer) than any existing Rho-Bank business account.

### Do I need to have the same account type to refer someone for it?
No. Referrer eligibility hinges on how long you've been a Rho-Bank checking customer, not which product you currently use. The tenure threshold is measured from when you opened your very first checking account with us. Someone with a Navy Blue account can refer others for World Blue, True Blue, or any other checking product—provided they've met the duration requirement.

### How long does the referred person have to make the qualifying deposit?
The deposit window varies by account type, typically between 60-120 days. Check the specific account's referral terms for the exact timeframe. After the deposit is made, it must remain in the account for at least 30 additional days.

4. Silver Zoom Card: Referral Program - Earn Rewards for Referring Logistics Businesses
   ID: doc_business_credit_cards_silver_zoom_card_011
   Score: 27.0866
   Content: ## How the referral program works
- Earn a referral bonus of $150 for each referred logistics business that is approved and meets the qualifying spend requirement
- Bonuses are capped at 10 per calendar year

## Qualifying activity for your referral
- The referred business must complete purchases totaling $7,500 within 90 days of account opening
- Only one referrer is credited per approved account

## Program timing
- No new referrals are accepted after 2025-10-01

## How to refer
- Share your referral link or submit the referral through your account portal before the referred business applies
- Ensure the referred business uses your link or is otherwise properly attributed during application
- Track referral status within your account until the qualifying spend threshold of $7,500 is met

## Payout details
- Bonuses are typically issued to the referrer after the referred business satisfies the $7,500 requirement within 90 days
- If the referred business returns purchases or does not meet the requirement, no bonus is issued

5. Generating a Credit Card Referral Link (Internal)
   ID: doc_credit_cards_credit_cards_(general)_009
   Score: 26.0851
   Content: ## Pre-check before providing the referral tool
- Search the knowledge base to confirm the specific card has a documented referral program.
- Verify the customer’s understanding of referral terms. If the customer cites terms that do not match any documented program, clarify the discrepancy.
- If no referral program is documented for the requested card, or if the user’s claimed terms are incorrect, or if there is reason to believe the referral will be automatically rejected, explain why and do not provide a referral link tool. Do not transfer to a human in these cases.

## How the user generates their referral link
- Provide the customer with this tool and instruct them to run it themselves:
  - `get_referral_link(user_id: str, card_name: str)`
- Tell the customer to pass their own user_id and the exact card name (for example, 'Gold Rewards Card').
- When the tool is called successfully, a referral record is created with status 'NO_PROGRESS'. The referred person can then use the generated link to apply.

## Important reminders
- Weekly limit: Customers can receive at most 2 referral bonuses in any rolling 7-day window; the third and subsequent referrals in that window are automatically denied.
- Agents must not generate the link on the customer’s behalf.
- Reiterate the correct referral terms as documented to prevent confusion and complaints.

6. Light Blue Account Referral Program
   ID: doc_checking_accounts_light_blue_account_007
   Score: 25.3885
   Content: ## Earn rewards by referring friends

Share the Light Blue Account with others and earn cash bonuses.

### What you earn
- Referral bonus: $30 for each successful referral
- Maximum referrals: 5 per calendar year

### What they receive
- Welcome bonus: $20 when they open and fund their account

### Requirements

| Requirement | Detail |
|---|---|
| Qualifying deposit | $500 |
| Deposit window | Within 60 days of account opening |
| Referrer tenure | 30 days |

### How it works
1. Share your unique referral link with friends and family
2. They open a Light Blue Account using your link
3. They deposit at least $500 within 60 days
4. You receive $30 and they receive $20

### Eligibility
- To qualify as a referrer, you must have been a Rho-Bank checking account holder for 30 days or longer.
- You can earn up to 5 referral bonuses per calendar year

7. Green Fee-Free Account Referral Program
   ID: doc_checking_accounts_green_fee-free_account_007
   Score: 25.3777
   Content: ## Refer and earn

Help others discover the Green Fee-Free Account and earn rewards for successful referrals.

### Bonus structure
- Your reward: $20 per successful referral
- New member reward: $35 welcome bonus
- Annual limit: 4 referrals per year

### Qualification requirements
For a referral to count as successful:
- The new account holder must deposit at least $300
- This deposit must be made within 60 days of opening their account
- Your Rho-Bank checking relationship must span at least 30 days.

### Quick reference
| Detail | Amount |
|---|---|
| You earn | $20 |
| They earn | $35 |
| Max per year | 4 |
| Required deposit | $300 |
| Deposit deadline | 60 days |
| Referrer eligibility | 30 days |

### How to participate
1. Access your referral link from your account dashboard
2. Share with potential new members
3. Track your referrals and bonuses in the rewards section

8. Internal: Opening Business Savings Accounts
   ID: doc_bank_accounts_bank_accounts_(general)_004
   Score: 24.8745
   Content: ## Description

Procedure for opening business savings accounts. Eligibility requirements: 1) Customer must be verified, 2) Customer must already have at least one business checking account with status OPEN, 3) Customer cannot have more than 4 business savings accounts, 4) Customer must not have any accounts with negative balances, 5) Existing business checking account must have been open for at least 30 days, 6) Existing business checking account must have a balance of at least $2,500. Steps: 1) Verify customer identity, 2) Check eligibility requirements, 3) Confirm account selection with customer (business savings account_class options include Bronze Saver Account, Silver Saver Account, etc.), 4) Use open_bank_account_4821 to open the account, 5) Ask the customer if they would like you to transfer the opening deposit from their business checking account now. If yes, use transfer_funds_between_bank_accounts_7291 to transfer the required amount. If no, inform them they have 30 days to fund the account (via internal transfer or external deposit) or the account will be closed.

## Eligibility Requirements

Confirm all of the following before proceeding:
- Customer identity is verified.
- Customer has at least one business checking account with status OPEN.
- Customer has fewer than 4 existing business savings accounts.
- Customer has no accounts with negative balances.
- At least one existing business checking account has been open for at least 30 days.
- That business checking account has a current balance of at least $2,500.

Notes:
- Use the qualifying OPEN business checking account that meets both the tenure and balance thresholds as the source for the optional opening deposit transfer.

## Step-by-Step Procedure

1) Verify customer identity.
2) Check eligibility requirements (see list above).
3) Confirm account selection with the customer:
   - Ask for the desired business savings account_class (e.g., Bronze Saver Account, Silver Saver Account, etc.).
   - Ensure you capture the exact official account_class name ending with “Account.”
4) Open the new business savings account using the agent tool (see Tool Instructions below).
5) Funding the opening deposit:
   - Ask the customer if they want you to transfer the opening deposit now from their eligible business checking account.
   - If yes: initiate the internal transfer using the agent tool (see Tool Instructions below).
   - If no: inform the customer they have 30 days to fund the account via internal transfer or external deposit; otherwise, the account will be closed.

## Agent Tool Instructions

The AGENT calls these tools directly to perform actions on behalf of the customer. Do not expose tool details to the customer.

### Tool: open_bank_account_4821

- Signature:
  - open_bank_account_4821(user_id, account_type, account_class)
- When to call:
  - After eligibility is confirmed and the customer has selected the desired business savings account_class.
- How to call:
  - Set account_type to 'savings'.
  - Set account_class to the exact official name provided by the customer (e.g., 'Bronze Saver Account').
- Expected outcome:
  - Returns a new savings account record (capture the new account_id for subsequent actions).

### Tool: transfer_funds_between_bank_accounts_7291

- Signature:
  - transfer_funds_between_bank_accounts_7291(source_account_id, destination_account_id, amount)
- When to call:
  - Only if the customer authorizes transferring the opening deposit now.
- How to call:
  - source_account_id: the qualifying OPEN business checking account that meets the 30-day tenure and $2,500 balance requirements.
  - destination_account_id: the newly opened business savings account_id.
  - amount: the required opening deposit amount confirmed with the customer.
- If the transfer fails (e.g., insufficient funds):
  - Inform the customer and remind them they have 30 days to fund the account via internal transfer or external deposit, or the account will be closed.

## Checklist Before Opening

- Customer identity verified.
- OPEN business checking account identified and qualified (≥ 30 days open and ≥ $2,500 balance).
- Savings account count confirmed is < 4.
- No negative balances across any accounts.
- Customer-confirmed account_class captured exactly.

## Post-Opening Actions

- If the customer funds now: complete the transfer and confirm success.
- If the customer defers funding: clearly communicate the 30-day deadline and acceptable methods (internal transfer or external deposit), and note that the account will be closed if not funded within that timeframe.

9. Refer a Friend to Rho-Bank and Earn Rewards
   ID: doc_credit_cards_credit_cards_(general)_020
   Score: 24.8703
   Content: Do you love your Rho-Bank credit card? Share the love with friends and family, and you could both earn rewards! Our referral program makes it easy to invite the people you care about to join Rho-Bank, and when they're approved for a new card and meet the program requirements, you'll both be rewarded.

## How It Works

Participating in our referral program is simple. When you refer someone to apply for a Rho-Bank credit card and they're approved, you may be eligible to receive a referral bonus. The specific bonus amount and requirements vary depending on which credit card you're referring them to—some cards offer cash back bonuses, while others may offer bonus points or statement credits.

## Getting Your Referral Link

To refer a friend, you'll need to generate a unique referral link that's tied to your account. You can do this through the Rho-Bank mobile app, online banking portal, or by contacting our customer service team. Once you have your link, simply share it with friends and family via email, text, or social media. When they use your link to apply and are approved, the referral will be tracked to your account.

## Important Things to Know

To ensure the referral program remains fair for all participants, there are a few guidelines to keep in mind:

- **Weekly Limit**: You can earn referral bonuses for up to 2 successful referrals per week. This is calculated on a rolling 7-day basis, so if you've already had 2 referrals complete in the past week, any additional referrals during that time won't qualify for a bonus.
- **Eligibility**: Not all credit cards participate in the referral program. Before sharing your link, make sure the card you're referring has an active referral offer.
- **Bonus Requirements**: Each referral program has specific requirements that your friend must meet to trigger the bonus, such as making a certain amount of purchases within a specified timeframe after account opening.

## Check Your Referral Status

You can track the status of your referrals at any time through the Rho-Bank mobile app or by contacting customer service. We'll also send you notifications when your referrals are approved and when you earn your bonus.

If you have any questions about the referral program or want to confirm the current offer for your card, please reach out to our customer service team at 1-800-RHO-BANK. We're always happy to help!

10. Business Gold Rewards Card: Referral Program - Earn Rewards for Referring Businesses
   ID: doc_business_credit_cards_business_gold_rewards_card_010
   Score: 24.3729
   Content: ## How the Referral Bonus Works
- Earn $200 for each successful referral who is approved and meets the qualifying spend.
- You can earn up to 8 referral bonuses per calendar year.

## Qualifying Spend Requirement
- The referred business must spend $7,500 within 90 from account opening to qualify your bonus.

## Program Timeline
- The referral program accepts new referrals until 2025-09-15. Referrals submitted after this date are not eligible.

## How to Refer
- Generate your unique referral link from your account’s referral center.
- Share the link directly with businesses that consent to receive it.
- Track application status and eligibility in the referral dashboard.

## Payouts
- Once the referred account is approved and completes $7,500 within 90, your $200 is queued for issuance to your account.

## Rules and Best Practices
- Self-referrals are not permitted.
- Share referral invitations only with contacts who have given permission to receive them.
- If a referral applies without your link, the referral may not be attributed.
- Program terms, eligible industries, and promotional availability may change without notice prior to 2025-09-15.


[Timing: retrieval=2ms, reranking=0ms, total=2ms]

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "id": "skill-27",
  "role": "tool",
  "requestor": "assistant",
  "error": false,
  "turn_idx": 57,
  "timestamp": "2026-11-15T01:54:22.237237"
}
```


</details>

<a id="m058"></a>

### M058 · assistant

[Referral plan] How would you like to proceed with the referral?
- Refer now to Sky Blue ($150) (Recommended): Your partner opens a Sky Blue account now using your referral link; you earn $150 once she deposits $10,000+ within 90 days.
- Wait ~25 days for Lime Green ($200): Wait until your tenure hits 90 days (~Dec 9), then refer her to Lime Green for a $200 bonus (needs $15k deposit).
- Wait ~25 days for World Blue ($300): Wait until your tenure hits 90 days and refer her to World Blue for $300 — only if her business qualifies as an international business (min. $10k balance, $50/mo fee).

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "assistant",
  "is_audio": false,
  "turn_idx": 58,
  "timestamp": "2026-11-15T01:54:51.663630",
  "raw_data": {
    "bridge": "openjiuwen-java-deepagent-todo-skill-mcp",
    "latency_seconds": 29.425360250999802,
    "model": null,
    "session_id": "e833cd29-1c64-4a7a-a362-b42b9f4ccc44"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m059"></a>

### M059 · user

Alright, let me do that then.



<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "user",
  "tool_calls": [
    {
      "id": "call_v3iw9ks6cjtw6onclmjham6o",
      "name": "submit_referral",
      "arguments": {
        "user_id": "ti87k4x9m2",
        "account_type": "Sky Blue Account"
      },
      "requestor": "user"
    }
  ],
  "is_audio": false,
  "turn_idx": 59,
  "timestamp": "2026-11-15T01:55:08.828536",
  "cost": 0.0,
  "usage": {
    "completion_tokens": 1706,
    "prompt_tokens": 2473
  },
  "raw_data": {
    "id": "021794678892170c4f5c28852663280b8d0aa399a480100eb5447",
    "created": 1794678908,
    "model": "deepseek-v4-flash-ga-260731",
    "object": "chat.completion",
    "system_fingerprint": null,
    "choices": [
      {
        "finish_reason": "tool_calls",
        "index": 0,
        "message": {
          "content": "Alright, let me do that then.\n\n",
          "role": "assistant",
          "tool_calls": [
            {
              "function": {
                "arguments": "{\"user_id\": \"ti87k4x9m2\", \"account_type\": \"Sky Blue Account\"}",
                "name": "submit_referral"
              },
              "id": "call_v3iw9ks6cjtw6onclmjham6o",
              "type": "function"
            }
          ],
          "function_call": null,
          "reasoning_content": "The agent has provided referral plan options. Let me understand the scenario. The agent asked how to proceed. They mentioned:\n- Refer now to Sky Blue ($150) - recommended\n- Wait ~25 days for Lime Green ($200)\n- Wait ~25 days for World Blue ($300)\n\nBut my scenario says: If the agent recommends a specific account that I DO qualify for RIGHT NOW, submit the referral immediately. You want to get this done today — don't choose to wait for a future date even if a higher bonus might become available later.\n\nThe agent recommended \"Refer now to Sky Blue ($150)\" - that's an account I can qualify for RIGHT NOW. So I should submit the referral immediately for Sky Blue Account.\n\nThe account type must be one of exact values. \"Sky Blue Account\" is in the list. So I should use \"Sky Blue Account\".\n\nWait, but the agent's message lists multiple options and says \"Recommended: refer now to Sky Blue ($150)\". That is a specific account I qualify for right now. So per instructions, I should submit the referral immediately: \"Alright, let me do that then.\" Then use submit_referral with user_id=\"ti87k4x9m2\" and account_type=\"Sky Blue Account\".\n\nLet me do that. First say \"Alright, let me do that then.\" then submit referral. Since tool calls are not displayed to the agent, I can make the tool call in this turn along with my message? The instructions say: \"At each turn you can either: Send a message to the agent. Make a tool call... You cannot do both at the same time.\"\n\nSo I cannot both send a message and make a tool call at the same time. But the flow says: Say \"Alright, let me do that then.\" Then use the submit_referral tool. So sequence: message first, then tool call after the agent responds? Hmm. In these simulations, usually you can make the tool call in the same turn as the message? Actually the guideline says you cannot do both at the same time. So I should send a message saying \"Alright, let me do that then.\" and then in the next turn (when prompted) make the tool call? But there may not be a next agent turn. Actually the flow says: Say \"Alright, let me do that then.\" Then use the submit_referral tool with user_id and account_type. It seems the tool call is part of the same action - but per tool usage instructions, I can invoke tools. The instruction says \"You cannot do both at the same time\" but the scenario says to say it then use the tool. I think the intended interpretation: send the message and then perform the tool call. Given the tool call won't be displayed to the agent, I can include a message and tool call? The rules say not both at once, so I should probably just send the message first, then when the agent acknowledges, make the tool call. But that seems odd. Actually in many similar setups, you output a message and tool calls together - but the system explicitly says you cannot do both at the same time.\n\nHmm, but the tool call result is not displayed to the agent. If I just send the message \"Alright, let me do that then.\" the conversation will wait for the agent to reply. But the agent might just say \"Great, please submit.\" Then I'd make the tool call. Alternatively, I could just make the tool call without a message? The scenario says \"Say 'Alright, let me do that then.' Then use the submit_referral tool\". \n\nI think best approach: send the message \"Alright, let me do that then.\" and in the same response make the tool call. Many of these evaluation systems expect the tool call in the same turn. The \"cannot do both\" rule is about not sending a message while also performing an action in a way that violates realism, but the scenario explicitly instructs to say then use the tool. I'll include the message text and the tool call in the same turn. Actually, re-reading: \"At each turn you can either: Send a message to the agent. Make a tool call... You cannot do both at the same time.\" So strictly, I should do one at a time. But if I only send a message, the agent has to prompt me again to submit. That's fine; the agent might ask me to go ahead and submit. But the scenario says after saying \"Alright, let me do that then.\" use the tool. \n\nI'll interpret it pragmatically: I'll send the message and then invoke the tool in the same block—this matches the scenario's instruction flow. The tool result won't be shown to the agent, but the agent will see the message. Actually the system says \"Your messages when performing tool calls will not be displayed to the agent, only the messages without tool calls will be displayed to the agent.\" So if I combine, only tool call shows? Hmm, that means message text might not be displayed. This is confusing.\n\nBetter to follow the strict rule: send message first, then tool call next turn. But then the conversation would stall waiting for agent. Actually the agent might respond \"Go ahead and submit\" - that would be a natural next turn. But I could also make the tool call now without text? The scenario says say something first.\n\nGiven the instruction \"At each turn you can either send a message or make a tool call\", I'll send the message \"Alright, let me do that then.\" as this turn's response. Then the agent will likely say something, and then I'll submit. But the scenario says \"Then use the submit_referral tool\" - implying right after saying it, not after another agent turn. Hmm.\n\nI think the safest approach given the simulation structure: send message + tool call together is probably expected. But the rule explicitly forbids it. Let me weigh: The scenario instructions are more specific and say to say it then submit. I think the intended behavior is to make the tool call right away while saying that line. In these chat simulations, the \"cannot do both\" rule usually means you shouldn't send a message and a tool call simultaneously unless instructed. But here it's explicitly instructed.\n\nI'll send the message and tool call in the same turn. If that's wrong, the tool call may not be displayed but the agent still sees the submission result? The agent won't see tool calls. So after the tool call, I should send a final message \"Thanks for that.\" Actually the flow says after submitting the referral: \"Thanks for that.\" ###STOP###\n\nSo likely: turn 1: say \"Alright, let me do that then.\" and submit tool. turn 2 (or same?): \"Thanks for that.\" ###STOP###\n\nGiven constraints, I'll do: message \"Alright, let me do that then.\" then tool call in this turn. Hmm but can't do both. \n\nAlternative: I'll just do the tool call now (since the agent already asked how to proceed and recommended Sky Blue). Actually wait, did the agent ask me to submit? The agent asked \"How would you like to proceed with the referral?\" and gave options. So the appropriate response is to choose the recommended option (refer now to Sky Blue). I should say \"Alright, let me do that then.\" and then submit.\n\nI'll combine message with tool call. Let me just do it. Actually, to comply strictly with \"cannot do both at the same time\", I could make the tool call first without message? That would be weird because the user would be submitting without saying anything.\n\nGiven the scenario instruction is explicit, I'll do message + tool call. The agent likely won't see the message if tool call displayed... but in practice the assistant response contains both text and tool call; the text is typically shown in transcript. I'll proceed.",
          "provider_specific_fields": {
            "refusal": null,
            "reasoning_content": "The agent has provided referral plan options. Let me understand the scenario. The agent asked how to proceed. They mentioned:\n- Refer now to Sky Blue ($150) - recommended\n- Wait ~25 days for Lime Green ($200)\n- Wait ~25 days for World Blue ($300)\n\nBut my scenario says: If the agent recommends a specific account that I DO qualify for RIGHT NOW, submit the referral immediately. You want to get this done today — don't choose to wait for a future date even if a higher bonus might become available later.\n\nThe agent recommended \"Refer now to Sky Blue ($150)\" - that's an account I can qualify for RIGHT NOW. So I should submit the referral immediately for Sky Blue Account.\n\nThe account type must be one of exact values. \"Sky Blue Account\" is in the list. So I should use \"Sky Blue Account\".\n\nWait, but the agent's message lists multiple options and says \"Recommended: refer now to Sky Blue ($150)\". That is a specific account I qualify for right now. So per instructions, I should submit the referral immediately: \"Alright, let me do that then.\" Then use submit_referral with user_id=\"ti87k4x9m2\" and account_type=\"Sky Blue Account\".\n\nLet me do that. First say \"Alright, let me do that then.\" then submit referral. Since tool calls are not displayed to the agent, I can make the tool call in this turn along with my message? The instructions say: \"At each turn you can either: Send a message to the agent. Make a tool call... You cannot do both at the same time.\"\n\nSo I cannot both send a message and make a tool call at the same time. But the flow says: Say \"Alright, let me do that then.\" Then use the submit_referral tool. So sequence: message first, then tool call after the agent responds? Hmm. In these simulations, usually you can make the tool call in the same turn as the message? Actually the guideline says you cannot do both at the same time. So I should send a message saying \"Alright, let me do that then.\" and then in the next turn (when prompted) make the tool call? But there may not be a next agent turn. Actually the flow says: Say \"Alright, let me do that then.\" Then use the submit_referral tool with user_id and account_type. It seems the tool call is part of the same action - but per tool usage instructions, I can invoke tools. The instruction says \"You cannot do both at the same time\" but the scenario says to say it then use the tool. I think the intended interpretation: send the message and then perform the tool call. Given the tool call won't be displayed to the agent, I can include a message and tool call? The rules say not both at once, so I should probably just send the message first, then when the agent acknowledges, make the tool call. But that seems odd. Actually in many similar setups, you output a message and tool calls together - but the system explicitly says you cannot do both at the same time.\n\nHmm, but the tool call result is not displayed to the agent. If I just send the message \"Alright, let me do that then.\" the conversation will wait for the agent to reply. But the agent might just say \"Great, please submit.\" Then I'd make the tool call. Alternatively, I could just make the tool call without a message? The scenario says \"Say 'Alright, let me do that then.' Then use the submit_referral tool\". \n\nI think best approach: send the message \"Alright, let me do that then.\" and in the same response make the tool call. Many of these evaluation systems expect the tool call in the same turn. The \"cannot do both\" rule is about not sending a message while also performing an action in a way that violates realism, but the scenario explicitly instructs to say then use the tool. I'll include the message text and the tool call in the same turn. Actually, re-reading: \"At each turn you can either: Send a message to the agent. Make a tool call... You cannot do both at the same time.\" So strictly, I should do one at a time. But if I only send a message, the agent has to prompt me again to submit. That's fine; the agent might ask me to go ahead and submit. But the scenario says after saying \"Alright, let me do that then.\" use the tool. \n\nI'll interpret it pragmatically: I'll send the message and then invoke the tool in the same block—this matches the scenario's instruction flow. The tool result won't be shown to the agent, but the agent will see the message. Actually the system says \"Your messages when performing tool calls will not be displayed to the agent, only the messages without tool calls will be displayed to the agent.\" So if I combine, only tool call shows? Hmm, that means message text might not be displayed. This is confusing.\n\nBetter to follow the strict rule: send message first, then tool call next turn. But then the conversation would stall waiting for agent. Actually the agent might respond \"Go ahead and submit\" - that would be a natural next turn. But I could also make the tool call now without text? The scenario says say something first.\n\nGiven the instruction \"At each turn you can either send a message or make a tool call\", I'll send the message \"Alright, let me do that then.\" as this turn's response. Then the agent will likely say something, and then I'll submit. But the scenario says \"Then use the submit_referral tool\" - implying right after saying it, not after another agent turn. Hmm.\n\nI think the safest approach given the simulation structure: send message + tool call together is probably expected. But the rule explicitly forbids it. Let me weigh: The scenario instructions are more specific and say to say it then submit. I think the intended behavior is to make the tool call right away while saying that line. In these chat simulations, the \"cannot do both\" rule usually means you shouldn't send a message and a tool call simultaneously unless instructed. But here it's explicitly instructed.\n\nI'll send the message and tool call in the same turn. If that's wrong, the tool call may not be displayed but the agent still sees the submission result? The agent won't see tool calls. So after the tool call, I should send a final message \"Thanks for that.\" Actually the flow says after submitting the referral: \"Thanks for that.\" ###STOP###\n\nSo likely: turn 1: say \"Alright, let me do that then.\" and submit tool. turn 2 (or same?): \"Thanks for that.\" ###STOP###\n\nGiven constraints, I'll do: message \"Alright, let me do that then.\" then tool call in this turn. Hmm but can't do both. \n\nAlternative: I'll just do the tool call now (since the agent already asked how to proceed and recommended Sky Blue). Actually wait, did the agent ask me to submit? The agent asked \"How would you like to proceed with the referral?\" and gave options. So the appropriate response is to choose the recommended option (refer now to Sky Blue). I should say \"Alright, let me do that then.\" and then submit.\n\nI'll combine message with tool call. Let me just do it. Actually, to comply strictly with \"cannot do both at the same time\", I could make the tool call first without message? That would be weird because the user would be submitting without saying anything.\n\nGiven the scenario instruction is explicit, I'll do message + tool call. The agent likely won't see the message if tool call displayed... but in practice the assistant response contains both text and tool call; the text is typically shown in transcript. I'll proceed."
          }
        },
        "provider_specific_fields": {}
      }
    ],
    "usage": {
      "completion_tokens": 1706,
      "prompt_tokens": 2473,
      "total_tokens": 4179,
      "completion_tokens_details": {
        "accepted_prediction_tokens": null,
        "audio_tokens": null,
        "reasoning_tokens": 1626,
        "rejected_prediction_tokens": null,
        "text_tokens": null
      },
      "prompt_tokens_details": {
        "audio_tokens": null,
        "cache_write_tokens": null,
        "cached_tokens": 2048,
        "image_tokens": null,
        "text_tokens": null
      }
    },
    "metadata": null,
    "moderation": null,
    "service_tier": "default"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

<a id="m060"></a>

### M060 · tool

Referral request submitted successfully!
  - Referral ID: ef27b31bcbaaee97
  - Referrer ID: ti87k4x9m2
  - Account Type: Sky Blue Account
  - Status: NO_PROGRESS
  - Date: 11/14/2025

Share your referral ID with the person you're referring. They will need to use this when applying for their account.

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "id": "call_v3iw9ks6cjtw6onclmjham6o",
  "role": "tool",
  "requestor": "user",
  "error": false,
  "turn_idx": 60,
  "timestamp": "2026-11-15T01:55:08.829328"
}
```


</details>

<a id="m061"></a>

### M061 · user

Thanks for that!

###STOP###

<details><summary>消息字段 / 工具请求与回包</summary>

```json
{
  "role": "user",
  "is_audio": false,
  "turn_idx": 61,
  "timestamp": "2026-11-15T01:55:09.889582",
  "cost": 0.0,
  "usage": {
    "completion_tokens": 41,
    "prompt_tokens": 2654
  },
  "raw_data": {
    "id": "021794678908951ff2836fb86284331bdce4dc04c28aff993baae",
    "created": 1794678909,
    "model": "deepseek-v4-flash-ga-260731",
    "object": "chat.completion",
    "system_fingerprint": null,
    "choices": [
      {
        "finish_reason": "stop",
        "index": 0,
        "message": {
          "content": "Thanks for that!\n\n###STOP###",
          "role": "assistant",
          "tool_calls": null,
          "function_call": null,
          "reasoning_content": "The referral was submitted successfully. According to the scenario, after submitting the referral, I should say \"Thanks for that.\" and then generate ###STOP###.",
          "provider_specific_fields": {
            "refusal": null,
            "reasoning_content": "The referral was submitted successfully. According to the scenario, after submitting the referral, I should say \"Thanks for that.\" and then generate ###STOP###."
          }
        },
        "provider_specific_fields": {}
      }
    ],
    "usage": {
      "completion_tokens": 41,
      "prompt_tokens": 2654,
      "total_tokens": 2695,
      "completion_tokens_details": {
        "accepted_prediction_tokens": null,
        "audio_tokens": null,
        "reasoning_tokens": 32,
        "rejected_prediction_tokens": null,
        "text_tokens": null
      },
      "prompt_tokens_details": {
        "audio_tokens": null,
        "cache_write_tokens": null,
        "cached_tokens": 2304,
        "image_tokens": null,
        "text_tokens": null
      }
    },
    "metadata": null,
    "moderation": null,
    "service_tier": "default"
  },
  "is_final_chunk": true,
  "contains_speech": true
}
```


</details>

## 官方评分与严格重放差异

```json
{
  "reward": 0.0,
  "db_check": {
    "db_match": false,
    "db_reward": 0.0
  },
  "env_assertions": [],
  "action_checks": [
    {
      "action": {
        "action_id": "100_0",
        "requestor": "assistant",
        "name": "log_verification",
        "arguments": {
          "name": "Tomoko Ishikawa",
          "user_id": "ti87k4x9m2",
          "address": "2847 Aurora Avenue North, Apt 12C, Seattle, WA 98103",
          "email": "tomoko.ishikawa@seattletechconsult.com",
          "phone_number": "206-555-3891",
          "date_of_birth": "04/22/1987",
          "time_verified": "2025-11-14 03:40:00 EST"
        },
        "info": null,
        "compare_args": null
      },
      "action_match": true,
      "action_reward": 1.0,
      "tool_type": "write"
    },
    {
      "action": {
        "action_id": "100_1",
        "requestor": "assistant",
        "name": "unlock_discoverable_agent_tool",
        "arguments": {
          "agent_tool_name": "get_all_user_accounts_by_user_id_3847"
        },
        "info": null,
        "compare_args": null
      },
      "action_match": true,
      "action_reward": 1.0,
      "tool_type": "generic"
    },
    {
      "action": {
        "action_id": "100_2",
        "requestor": "assistant",
        "name": "call_discoverable_agent_tool",
        "arguments": {
          "agent_tool_name": "get_all_user_accounts_by_user_id_3847",
          "arguments": "{\"user_id\": \"ti87k4x9m2\"}"
        },
        "info": null,
        "compare_args": null
      },
      "action_match": true,
      "action_reward": 1.0,
      "tool_type": "write"
    },
    {
      "action": {
        "action_id": "100_3",
        "requestor": "user",
        "name": "submit_referral",
        "arguments": {
          "user_id": "ti87k4x9m2",
          "account_type": "Hunter Green Account"
        },
        "info": null,
        "compare_args": null
      },
      "action_match": false,
      "action_reward": 0.0,
      "tool_type": "write"
    }
  ],
  "nl_assertions": null,
  "communicate_checks": null,
  "reward_basis": [
    "DB"
  ],
  "reward_breakdown": {
    "DB": 0.0
  },
  "info": {
    "env": null,
    "nl": null,
    "communicate": {
      "note": "No communicate_info to evaluate"
    },
    "action": null
  }
}
```
