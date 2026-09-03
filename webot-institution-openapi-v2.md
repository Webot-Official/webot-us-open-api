# Webot US Institution Open API Documentation (v2)

HTTP API reference for institutional service providers (`/api/v2/institution/*`). An institution uses **its own API Key (an RSA or Ed25519 key pair)** to onboard and operate the sub-accounts (`userId`) bound to it — fiat deposit/withdrawal, stablecoin conversion, on-chain assets, and trading-account balances.

> This is the **v2** institution reference. Unlike v1 ([webot-institution-openapi.md](./webot-institution-openapi.md)), v2 uses **public-key signature authentication** (RSA or Ed25519) and identifies the target sub-account by **`userId`** (a UUID) rather than `uid`. Authentication is documented in full below — v2 does **not** share the v1 authentication section.

## End-to-End Flow

The diagram below shows the full path from registering your public key to moving money on a sub-account. **Phases 1–4 are the onboarding spine** (sequential): [Authentication](#authentication) → [Create Sub-Account](#1-create-sub-account) → [Platform KYB](#kyb-endpoints) → [Channel Onboarding](#4-onboard-a-deposit-account-channel-kyb). Once the sub-account is operational, the money-movement flows are **independent capabilities you can call in any order**: [deposit](#deposit-endpoints), [fiat payout](#payout-endpoints) (create a payee account and wait for it to reach `AVAILABLE`, then submit the payout), [on-chain withdrawal](#asset-on-chain-endpoints) (whitelist an address, then withdraw), and [convert](#convert-endpoints) / [balances](#account-endpoints).

![Webot Institution Open API v2 end-to-end flow](./webot-institution-openapi-v2-onboarding.svg)

> **Key gate:** all `wire/*` endpoints require the target `userId`'s platform KYB to be `APPROVED` first — see the [KYB precondition](#kyb-endpoints).

## General Information

| | |
|---|---|
| Base URL | `https://api.webot.com` |
| Protocol | HTTPS |
| Data Format | JSON |
| Field Naming | camelCase (e.g. `userId`, `clientOrderId`) |
| Amounts | decimal strings (e.g. `"100.50"`) — never float, never minor-unit integers |
| Timestamps | millisecond Unix timestamp (`int64`) in **response bodies**; the signature `timestamp` query parameter is in **seconds** (see Authentication) |
| Currency codes | ISO 4217 uppercase (`"USD"`); country codes ISO 3166-1 alpha-2 uppercase (`"US"`) |

### Response Envelope

All endpoints return a uniform envelope.

**Success:**

```json
{ "result": true, "timestamp": 1785706000000, "data": { } }
```

**Failure:**

```json
{ "result": false, "timestamp": 1785706000000, "code": "P_PAY_OPEN_API_INVALID_ARGUMENT", "message": "..." }
```

Business failures are returned as HTTP `200` with `result: false`. The only two exceptions come from the authentication layer: `401` (authentication failed) and `400` (request body could not be read).

### Endpoint Summary

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v2/institution/user/create` | Create a sub-account (user) |
| GET | `/api/v2/institution/users` | List sub-accounts |
| POST | `/api/v2/institution/kyb/create` | Submit platform KYB |
| GET | `/api/v2/institution/kyb` | Get platform KYB status |
| GET | `/api/v2/institution/wire/deposit/account/requirements` | Get channel onboarding requirements |
| POST | `/api/v2/institution/wire/deposit/account/create` | Onboard a deposit account (channel KYB) |
| GET | `/api/v2/institution/wire/deposit/account` | Get deposit-account onboarding status |
| GET | `/api/v2/institution/wire/deposit/accounts` | List deposit accounts |
| GET | `/api/v2/institution/wire/deposit/orders` | List deposit orders |
| GET | `/api/v2/institution/wire/deposit/order` | Get a deposit order |
| GET | `/api/v2/institution/wire/payout/account/requirements` | Get payout-account field requirements |
| POST | `/api/v2/institution/wire/payout/account/create` | Create a payout (payee) account |
| GET | `/api/v2/institution/wire/payout/accounts` | List payout accounts |
| POST | `/api/v2/institution/wire/payout/account/update` | Update a payout account |
| POST | `/api/v2/institution/wire/payout/account/delete` | Delete a payout account |
| POST | `/api/v2/institution/wire/payout/order/create` | Create a payout (fiat withdrawal) |
| GET | `/api/v2/institution/wire/payout/orders` | List payout orders |
| GET | `/api/v2/institution/wire/payout/order` | Get a payout order |
| GET | `/api/v2/institution/asset/currencies` | List currencies and chains |
| POST | `/api/v2/institution/asset/withdraw` | Create an on-chain withdrawal |
| GET | `/api/v2/institution/asset/withdraw` | Query a single on-chain withdrawal |
| GET | `/api/v2/institution/asset/records` | Query deposit/withdrawal history |
| GET | `/api/v2/institution/addressBooks` | List address-book entries |
| POST | `/api/v2/institution/addressBook` | Add an address-book entry |
| POST | `/api/v2/institution/addressBook/delete` | Delete an address-book entry |
| GET | `/api/v2/institution/account/balances` | Get trading-account balances |
| POST | `/api/v2/institution/convert/order/create` | Create a conversion |
| GET | `/api/v2/institution/convert/orders` | List conversion orders |
| GET | `/api/v2/institution/convert/order` | Get a conversion order |
| POST | `/api/v2/institution/file/upload` | Upload a file (KYB / supporting documents) |
| GET | `/api/v2/institution/file/download` | Download a file |

---

## Authentication

Every request (except where noted) is authenticated with your institution API Key and a **signature**. Apply for an API Key by registering your **public key** with Webot; you keep the private key.

### Headers

| Header | Description |
|--------|-------------|
| `X-APIKEY` | Your API Key, in the form `webot_xxxxxxxx`. Used to look up your registered public key. |
| `X-Signature` | Base64 (standard encoding) of the signature over the canonical string below. |

### Signature algorithms

The algorithm is determined by the **type of public key you registered** — you do not choose it per request. Two key types are supported:

| Key type | How to sign | Notes |
|----------|-------------|-------|
| **RSA** | RSA-PSS over the **SHA-256** digest | 2048–4096-bit key. Salt length 32 recommended (20 / 32 / 64 all accepted). **Not** PKCS#1 v1.5. |
| **Ed25519** | Sign the message bytes **directly** | Do **not** pre-hash — EdDSA already includes SHA-512. |

- Register the public key in **PKIX/SPKI** form (`-----BEGIN PUBLIC KEY-----`). PKCS#1 "RSA PUBLIC KEY" and other algorithms (ECDSA, DSA, …) are not accepted.
- RSA reference: Go `rsa.SignPSS(rand, priv, crypto.SHA256, sha256(msg), nil)`; OpenSSL `-sigopt rsa_padding_mode:pss`.

### Required query parameter

| Parameter | Type | Description |
|-----------|------|-------------|
| `timestamp` | integer | Current time in **seconds** (Unix). Required on every signed request and participates in the signature. Must be within **±5 seconds** of server time, otherwise the request is rejected. |

> `timestamp` goes in the **query string** on every request, including `POST` (whose business payload is in the JSON body). There is **no** `client_id` / nonce parameter.

### Canonical string

Sign the following string:

```
{sub_path}:{sorted_query_string}:{request_body}:{timestamp}
```

| Segment | Construction |
|---------|--------------|
| `sub_path` | The request path, verbatim (not URL-encoded), e.g. `/api/v2/institution/account/balances`. |
| `sorted_query_string` | Percent-encode each key and value **separately** with `encodeURIComponent` semantics — do **not** escape `A-Za-z0-9 - _ . ! ~ * ' ( )`, hex digits uppercase, space is `%20` (do not use form-encoding, which emits `+`). Join each as `key=value`, then **sort the `key=value` strings** and join with `&`. Every query parameter participates — `timestamp` plus business params such as `userId`; repeated keys are kept and sorted by value. |
| `request_body` | For `POST` with a JSON body: the raw body, verbatim (not re-serialized). For `GET`: the empty string (so the canonical string shows `::`). |
| `timestamp` | The same seconds value, appended again at the end. |

**Examples:**

```
GET  (no body):   /api/v2/institution/account/balances:timestamp=1785706000&userId=88001234::1785706000
POST (JSON body): /api/v2/institution/kyb/create:timestamp=1785706000:{"userId":"88001234"}:1785706000
```

Then `X-Signature = base64( sign( canonical_string ) )`, sent together with `X-APIKEY`.

The diagram below summarizes where each parameter comes from, how `sorted_query_string` is built, and how the four segments concatenate. Mixing up a parameter's source is the most common integration error.

![Webot Institution Open API v2 canonical string construction](./webot-institution-openapi-v2-signature.svg)

---

## Permissions (Scopes)

Each API Key is granted one or more **scopes** at registration (default: `read`). Every endpoint requires a scope; a request whose key lacks the required scope is rejected with `P_PAY_OPEN_API_PERMISSION_DENIED` and never reaches business logic.

- **Read** endpoints (the `GET` queries — balances, orders, records, requirements, status, lists) require read access.
- **State-changing** endpoints (`POST` create / submit / update / delete — sub-account and KYB onboarding, payouts, on-chain withdrawals, conversions, address-book and file writes) require the corresponding **write** scope.

Contact Webot to grant your key the scopes your integration needs; the scopes attached to a key cannot be changed by the caller.

---

## The `userId` Parameter

Except for public/self endpoints (create user, list users, `asset/currencies`), **every endpoint requires `userId`** — the UUID of the target sub-account:

- **GET requests:** pass `userId` in the query string (it participates in the signature);
- **POST requests with a JSON body:** pass `userId` in the JSON request body;
- **File upload** (`multipart/form-data`): pass `userId` in the query string.

Obtain `userId` values from [List Sub-Accounts](#2-list-sub-accounts) (or the response of [Create Sub-Account](#1-create-sub-account)).

---

## Error Codes

Codes below may be returned by any endpoint (base set). Endpoint-specific business codes are listed with the relevant endpoint.

| Error Code | Description |
|------------|-------------|
| `P_PAY_OPEN_API_INVALID_ARGUMENT` | A request parameter is missing or invalid. |
| `P_PAY_OPEN_API_UNAUTHENTICATED` | Authentication failed (missing key, bad signature, etc.). Returns HTTP `401`. |
| `P_PAY_OPEN_API_PERMISSION_DENIED` | Your API Key lacks permission for this endpoint. |
| `P_PAY_OPEN_API_NOT_FOUND` | Resource does not exist, or does not belong to this user. |
| `P_PAY_OPEN_API_ALREADY_EXISTS` | Resource already exists (e.g. address already in the address book). |
| `P_PAY_OPEN_API_SERVICE_UNAVAILABLE` | A dependency is temporarily unavailable; retry later. |
| `P_PAY_OPEN_API_TIMEOUT` | The request timed out; retry later. |
| `P_PAY_OPEN_API_INTERNAL_ERROR` | Internal error. |
| `P_PAY_OPEN_API_OPERATION_NOT_SUPPORTED` | The channel does not support this operation. Do not retry. |
| `P_PAY_OPEN_API_CHANNEL_NOT_SUPPORTED_IN_REGION` | The requested `channel` is not available for your integration. Do not retry with the same channel. |

---

## User Endpoints

### 1. Create Sub-Account

Create a sub-account (user) bound to your institution. Idempotent by `clientId`.

```
POST /api/v2/institution/user/create
```

**Request Body (JSON):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| clientId | string | Yes | Client-defined idempotency key, max 64 chars. Retries must reuse the same value. |
| email | string | Yes | Email, max 64 chars. |
| entityType | string | Yes | `CORPORATE` (business) / `INDIVIDUAL` (natural person). |
| remark | string | No | Note, max 100 chars. |

**Response Example:**

```json
{ "result": true, "timestamp": 1785706000000, "data": { "userId": "88001234-1a2b-..." } }
```

**Errors:**

| Error Code | Description |
|------------|-------------|
| `P_PAY_OPEN_API_SUB_USER_CREATE_FORBIDDEN` | Master account unavailable, caller is itself a sub-account (nesting unsupported), or sub-account limit reached. |
| `P_PAY_OPEN_API_SUB_USER_ACCOUNT_CREATE_FAILED` | The sub-account was created but not fully set up. `data.userId` returns the created id; resend the identical request to complete setup. |

### 2. List Sub-Accounts

```
GET /api/v2/institution/users
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| page | integer | No | Page number, starting from 1. |
| size | integer | No | Page size, default 100, max 500. |

**Response Example:**

```json
{
  "result": true,
  "timestamp": 1785706000000,
  "data": {
    "list": [
      { "userId": "88001234-...", "email": "a@example.com", "entityType": "CORPORATE", "status": "ACTIVE", "remark": "Client A", "createTime": 1785700000000 }
    ],
    "total": 1
  }
}
```

> `total` is the total count for pagination. An out-of-range page returns an empty `list` with the real `total`.

---

## KYB Endpoints

Onboarding is a **two-step** flow:

1. **Platform KYB** — submit company/representative information once via `POST /kyb/create`. It must reach status `APPROVED` before any channel deposit onboarding.
2. **Channel onboarding** — once platform KYB is approved, onboard a deposit account with a specific channel via `wire/deposit/account/*`.

> **Precondition:** all `wire/*` endpoints (channel deposit onboarding, deposit accounts/orders, payout accounts, payouts) require the `userId`'s **platform KYB to be `APPROVED`**. Otherwise `P_PAY_OPEN_API_INTERNAL_KYB_NOT_APPROVED` is returned.

### How to fill KYB fields

Platform KYB and channel KYB use **different** field sources — fill them accordingly.

#### Platform KYB fields (`POST /kyb/create`)

Platform KYB fields follow a **fixed, documented field list** — fill them according to this documentation, not by calling an endpoint. Every item has a **canonical key** in a flat key space:

- Subject (company) fields use the `subject.` prefix; each is one `{ "key": "...", "value": "..." }` under `subject.fields`.
- Each related natural person uses the `representative.` prefix; submit one entry per person under `representatives[]`, distinguished by the `representativeRef` property.
- Documents share the same key space (their key is the document's purpose) and carry a `fileId` — upload first (see [File Endpoints](#file-endpoints)), then reference by `fileId`.

The complete field list, required markers, formats, conditional rules, enums, and the document matrix are in **[Platform KYB Field Reference](#platform-kyb-field-reference)** below.

#### Channel KYB fields (`wire/deposit/account/*`)

> **`channel` currently supports only `bridge`.**

Channel KYB fields are **dynamic** — **call `GET /wire/deposit/account/requirements` first**, then fill per the returned `Requirement` items. Do not hard-code channel field lists.

- **`mode`** is the source of truth for whether to submit an item: `REQUIRED` (must submit), `OPTIONAL`, or `CONDITIONAL`.
- **`CONDITIONAL`** means the item becomes required only when other fields take certain values; when unsure, submit it. The final decision rests with the channel.
- **`kind`** is `FIELD` or `DOCUMENT`. Documents are referenced by `fileId` (upload first — see [File Endpoints](#file-endpoints)); do not inline file bytes.
- Representatives are grouped by `representativeRef`; fill each representative's own `fields` / `documents`.
- `regex` / `example` / `enumValues` on a field are for client-side validation and hints.
- The requirements endpoint returns the items still required for the selected channel; information already provided is omitted. **Documents must be submitted in full.**

> The exact fields and documents each channel requires — with their formats — are returned by the requirements endpoint. Render your form from that response rather than hard-coding a list.

### 1. Submit Platform KYB

```
POST /api/v2/institution/kyb/create
```

**Request Body (JSON):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| userId | string | Yes | Sub-account UUID. A `userId` has a single platform KYB application; resubmitting updates it while it is still under review. Once `APPROVED`, it can no longer be resubmitted. |
| subject | object | No | Subject fields: `{ "fields": [ { "key": "...", "value": "..." } ] }`. Keys are canonical keys. |
| representatives | object[] | No | Each: `{ "representativeRef": "...", "fields": [ ... ] }`. |
| documents | object[] | No | Each: `{ "purpose": "...", "fileId": "...", "scope": "SUBJECT|REPRESENTATIVE", "representativeRef": "..." }`. |

**Response Example:**

```json
{ "result": true, "timestamp": 1785706000000, "data": { "status": "SUBMITTED" } }
```

Validation (key validity + unconditional required + enum) passing returns `SUBMITTED`; otherwise `P_PAY_OPEN_API_INVALID_ARGUMENT` and nothing is stored.

**Errors:**

| Error Code | Description |
|------------|-------------|
| `P_PAY_OPEN_API_KYB_ALREADY_APPROVED` | Platform KYB is already `APPROVED` and can no longer be resubmitted. |
| `P_PAY_OPEN_API_KYB_SUBMIT_IN_PROGRESS` | A submission for this `userId` is already being processed; retry later. |

### 2. Get Platform KYB Status

```
GET /api/v2/institution/kyb
```

**Request Parameters:** `userId` (string, required).

**Response Example:**

```json
{ "result": true, "timestamp": 1785706000000, "data": { "status": "APPROVED", "reason": "", "message": "" } }
```

| Field | Type | Description |
|-------|------|-------------|
| status | string | `SUBMITTED` / `PENDING` / `SUPPLEMENT_REQUIRED` / `APPROVED` / `REJECTED`. |
| reason | string | Review conclusion code; empty before review. |
| message | string | Conclusion description; empty before review. |

### 3. Get Channel Onboarding Requirements

Returns the items still required for channel onboarding. Information already provided is omitted. Representative requirements are returned per contact.

```
GET /api/v2/institution/wire/deposit/account/requirements
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| userId | string | Yes | Sub-account UUID. |
| channel | string | Yes | Channel identifier. Currently only `bridge` is supported. |

> Do not pass `country` or `businessType` — the requirement set follows the values from your platform KYB (`subject.country` / `subject.businessType`).

**Response Fields (`data`):**

| Field | Type | Description |
|-------|------|-------------|
| subjectFields | Requirement[] | Subject fields still missing (what your platform KYB has not already provided). |
| subjectDocuments | Requirement[] | Subject documents still missing (flattened, one per purpose). |
| requiresRepresentatives | boolean | Whether representative info is required. |
| representatives | object[] | What each contact still needs, one entry per contact: `{ representativeRef, fields[], documents[] }`. Contacts already on file are returned **with their `representativeRef`** — reuse that value when submitting. If there is no contact yet, a single entry with an empty `representativeRef` and the full template is returned, to fill in your first contact. |
| fileLimit | object | `{ maxFileCount, maxFileBytes, maxTotalBytes, contentTypes[] }`. |
| tosMode | string | `NONE` / `HOSTED_LINK` / `INLINE_ACCEPT`. |
| tosUrl | string | Terms URL; empty when `NONE`. |
| termsVersion | string | Terms version; non-empty only for `INLINE_ACCEPT`. |
| requiresBusinessType | boolean | Whether a business type is still needed to refine the list. Always `false` in this API — the business type comes from platform KYB. |

`Requirement`: `{ key, kind (FIELD|DOCUMENT), mode (REQUIRED|OPTIONAL|CONDITIONAL), label, regex, example, enumValues[] }`. Use `mode` to decide whether to submit an item (`REQUIRED` → must submit).

### 4. Onboard a Deposit Account (Channel KYB)

Submit channel onboarding. Returns onboarding `status` only; missing/invalid items are not itemized — call the requirements endpoint to learn what is still missing.

```
POST /api/v2/institution/wire/deposit/account/create
```

**Request Body (JSON):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| userId | string | Yes | Sub-account UUID. |
| channel | string | No | Channel. Currently only `bridge` is supported. |
| signedAgreementId | string | Cond. | For `tosMode = HOSTED_LINK`. |
| acceptedTerms | boolean | Cond. | For `tosMode = INLINE_ACCEPT`. |
| termsVersion | string | Cond. | For `tosMode = INLINE_ACCEPT`. |
| subject | object | No | `{ "fields": [ { "key", "value" } ] }`. |
| representatives | object[] | No | `[ { "representativeRef", "fields": [...] } ]`. |
| documents | object[] | No | **Provide all required documents in full every time.** Each: `{ purpose, fileId, scope, representativeRef }`. |

> Do not pass `country` or `businessType` here either — they come from your platform KYB. Any `fileId` you reference must belong to this `userId`.

**Response Example:**

```json
{ "result": true, "timestamp": 1785706000000, "data": { "status": "IN_REVIEW" } }
```

`status`: `NOT_CREATED` / `SUBMITTED` / `IN_REVIEW` / `ACTION_REQUIRED` / `APPROVED` / `REJECTED`.

**Errors:**

| Error Code | Description |
|------------|-------------|
| `P_PAY_OPEN_API_INTERNAL_KYB_NOT_APPROVED` | Platform KYB is not approved yet; it must be approved before channel onboarding. |
| `P_PAY_OPEN_API_KYB_ADDRESS_REJECTED` | Address rejected by the channel; `data.violations` names the rejected fields. |
| `P_PAY_OPEN_API_KYB_DOCUMENT_REJECTED` | A document was rejected or a required field is missing. |
| `P_PAY_OPEN_API_KYB_SUBJECT_TYPE_CONFLICT` | Another subject type already exists for this `userId`. |
| `P_PAY_OPEN_API_KYB_MANUAL_REVIEW_REQUIRED` | Additional review is required; do not resubmit with altered details. |
| `P_PAY_OPEN_API_KYB_SUBJECT_NOT_FOUND` | No matching company record was found. |

### 5. Get Deposit-Account Onboarding Status

```
GET /api/v2/institution/wire/deposit/account
```

**Request Parameters:** `channel` (string, required; currently only `bridge` is supported). `status = NOT_CREATED` means not yet onboarded (not an error). Response `data`: `{ "status": "..." }` (same enum as above).

---

## Platform KYB Field Reference

The canonical fields and documents accepted by `POST /kyb/create`. Applies to companies registered in **Hong Kong (HK)** or the **United States (US)**.

### Required markers

| Marker | Meaning |
|--------|---------|
| **M** | Mandatory — a missing value fails validation (`P_PAY_OPEN_API_INVALID_ARGUMENT`). |
| **C** | Conditional — required when the trigger in the description holds. |
| **O** | Optional — providing it speeds up review; omitting it does not block. |

> The `HK` / `US` columns give the marker per jurisdiction (`subject.country`). `N/A` means the field is ignored for that jurisdiction. Files are submitted as `documents[]` with the document's canonical key as `purpose` and a `fileId`.

### Submission structure

```json
{
  "userId": "88001234-....",
  "subject": { "fields": [ { "key": "subject.legalNameEn", "value": "Acme Ltd." }, ... ] },
  "representatives": [ { "representativeRef": "PERSON-01", "fields": [ { "key": "representative.firstName", "value": "..." }, ... ] } ],
  "documents": [ { "purpose": "subject.sourceOfFundsProof", "fileId": "...", "scope": "SUBJECT" },
                 { "purpose": "representative.passport", "fileId": "...", "scope": "REPRESENTATIVE", "representativeRef": "PERSON-01" } ]
}
```

### 1. Subject fields (`subject.*`)

| Key | HK | US | Rules |
|-----|:--:|:--:|-------|
| `subject.country` | M | M | Registration jurisdiction. `HK` / `US`. Drives all validation. |
| `subject.legalNameEn` | M | M | Legal English name, ≤200. Must match the registration document exactly (incl. `Limited`/`Ltd.`/`Inc.` suffix). Non-Latin names need an official English translation. |
| `subject.legalNameCn` | O | N/A | Legal Chinese name, ≤100. HK companies registered in Chinese should provide it; N/A for US. |
| `subject.registrationNo` | M | M | HK: Business Registration No.; US: IRS EIN (format `XX-XXXXXXX`). ≤32. |
| `subject.registrationNoType` | M | M | `BRN` (HK) / `EIN` (US). Must match `subject.country`. |
| `subject.businessType` | M | M | Org form (enum §[Enums](#5-enums)). Also determines which US charter document is required (see §[Documents](#2-subject-documents-subject)). |
| `subject.incorporationDate` | M | M | `yyyy-MM-dd`. Companies incorporated < 6 months may enter enhanced due diligence. |
| `subject.incorporationState` | N/A | M | US state code (e.g. `DE`, `CA`). US only. |
| `subject.email` | M | M | Official business email, ≤128. A free-email domain (gmail/qq/163…) triggers manual review. |
| `subject.phone.countryCode` | C | C | Intl. dialing code without `+` (e.g. `852`, `1`). Required if phone is provided. |
| `subject.phone.number` | C | C | Required if phone is provided. ≤20. |
| `subject.website` | O | O | Must include scheme (`https://`), ≤256. Recommended for e-commerce/platform businesses. |
| `subject.notifyUrl` | O | O | Review-result callback URL. |
| `subject.registeredAddress.addressLine1` | M | M | Street + number, ≤200. **No P.O. Box**; US must include a street number. |
| `subject.registeredAddress.addressLine2` | O | O | Room/floor/unit, ≤200. |
| `subject.registeredAddress.city` | M | M | ≤100. |
| `subject.registeredAddress.state` | O | M | 2-letter state code (e.g. `NY`). US mandatory; HK may omit. |
| `subject.registeredAddress.postalCode` | O | M | US mandatory; HK has no postal codes. |
| `subject.registeredAddress.countryCode` | M | M | ISO 3166-1 alpha-2. |
| `subject.operatingAddressSameAsRegistered` | M | M | `true` / `false`. When `true`, omit `operatingAddress`. |
| `subject.operatingAddress.*` | C | C | Same sub-fields as `registeredAddress`. Required when `operatingAddressSameAsRegistered = false`. |
| `subject.businessDescription` | M | M | Concrete description of products/services, ≤500. Vague terms ("trading", "consulting") are rejected for supplement. |
| `subject.accountPurpose.cryptoTrading` | O | O | `true`/`false`. At least one `accountPurpose.*` should be `true`. |
| `subject.accountPurpose.fiatDeposit` | O | O | `true`/`false`. |
| `subject.accountPurpose.fiatWithdrawal` | O | O | `true`/`false`. |
| `subject.accountPurpose.cardIssuing` | O | O | `true`/`false`. |
| `subject.accountPurpose.crossBorderPayment` | O | O | `true`/`false`. |
| `subject.accountPurpose.fxConversion` | O | O | `true`/`false`. |
| `subject.accountPurpose.payroll` | O | O | `true`/`false`. |
| `subject.accountPurpose.other` | O | O | `true`/`false`; describe in `businessDescription`. |
| `subject.monthlyDepositLimit.amount` | M | M | Decimal string, ≤2 decimals. Recommended in USD. |
| `subject.monthlyDepositLimit.currency` | M | M | ISO 4217. |
| `subject.monthlyWithdrawalLimit.amount` | M | M | Decimal string, ≤2 decimals. |
| `subject.monthlyWithdrawalLimit.currency` | M | M | ISO 4217. |
| `subject.pepDeclaration.hasPepRelation` | M | M | `true`/`false`. Whether any director/shareholder/UBO (or close relation) is/was a politically exposed person. |
| `subject.pepDeclaration.description` | C | C | Required when `hasPepRelation = true`, ≤500. Names, positions, tenure. |
| `subject.ownershipDeclaration.hasShareholderOver25Percent` | C | C | `true`/`false`. Required when no document evidencing the ownership structure is submitted. When `true`, `representatives[]` must include at least one person with `role.responsibility = ULTIMATE_BENEFICIAL_OWNER`. |
| `subject.ownershipDeclaration.hasNomineeShareholder` | O | O | `true`/`false`. If `true`, disclose the ultimate beneficial owner. |
| `subject.highRiskCountryExposure.involved` | O | O | `true`/`false`. Whether business touches FATF high-risk jurisdictions. |
| `subject.highRiskCountryExposure.description` | C | C | Required when `involved = true`, ≤500. |
| `subject.termsAgreed` | M | M | Must be `true`, else the application is rejected. |
| `subject.dataUsageAgreed` | M | M | Must be `true` (authorizes third-party data verification). |
| `subject.serviceAgreementType` | M | M | `FULL` / `RECIPIENT` (enum §[Enums](#5-enums)). |
| `subject.signerPersonRefId` | M | M | Must equal the `representativeRef` of the person designated as the authorized signer. |
| `subject.agreedAt` | M | M | ISO 8601 (e.g. `2026-08-25T10:12:33Z`). |
| `subject.deviceData.ipAddress` | M | M | Signer's public IP at consent time (IPv6-compatible), ≤45. |
| `subject.deviceData.userAgent` | M | M | Signer's User-Agent, ≤512. |

### 2. Subject documents (`subject.*`)

Value is a `fileId`. Required matrix by jurisdiction:

| Key | HK | US | Notes |
|-----|:--:|:--:|-------|
| `subject.businessRegistrationCertificate` | M | N/A | Business Registration Certificate (BR). |
| `subject.businessFormation` | M | M | Certificate of Incorporation (HK CI / US Certificate of Incorporation, issued by the Secretary of State). |
| `subject.incorporationFormNnc1` | C | N/A | Incorporation Form NNC1. **Note 1**. |
| `subject.annualReturnNar1` | C | N/A | Annual Return NAR1. **Note 1**. |
| `subject.einConfirmationLetter` | N/A | M | IRS EIN confirmation letter (CP575 / 147C). |
| `subject.bylaws` | N/A | C | Charter — when `businessType` is a corporation subtype (`B_CORPORATION` / `C_CORPORATION` / `CLOSE_CORPORATION` / `S_CORPORATION`). **Note 4**. |
| `subject.operatingAgreement` | N/A | C | Charter — when `businessType = LLC`, or the merged fallback when `businessType` is not provided. **Note 4**. |
| `subject.partnershipAgreement` | N/A | C | Charter — when `businessType = LLP` / `LP` / `GENERAL_PARTNERSHIP`. **Note 4**. |
| `subject.registerOfDirectors` | C | C | Register of directors. **Note 2**. |
| `subject.ownershipProof` | C | C | Register of shareholders. **Note 2**. |
| `subject.shareholdingStructureChart` | C | C | Shareholding structure chart. **Note 2, Note 3**. |
| `subject.certificateOfGoodStanding` | N/A | O | Certificate of good standing. |
| `subject.financialStatements` | O | O | Financial statements. |
| `subject.authorizationLetter` | O | O | Authorization letter. |
| `subject.sourceOfFundsProof` | M | M | Source-of-funds proof — see **Note 5**. |
| `subject.supportiveOther` | O | O | Other supporting materials. |
| `subject.bankStatement` | O | O | Address proof: bank statement. |
| `subject.utilityBill` | O | O | Address proof: utility bill. |
| `subject.leaseAgreement` | O | O | Address proof: lease agreement. |
| `subject.taxNotice` | O | O | Address proof: tax authority notice. |
| `subject.addressProofOther` | O | O | Address proof: other. |

**Conditional rules:**

- **Note 1 (HK charter docs):** submit at least one of `incorporationFormNnc1` / `annualReturnNar1`. If incorporated over a year, `annualReturnNar1` (latest directors/shareholders/address) is preferred.
- **Note 2 (ownership & directors):** submit at least one of `registerOfDirectors` / `ownershipProof` / `shareholdingStructureChart` that fully shows directors and ownership. If already evidenced by NNC1/NAR1 (HK) or the charter document (US), it may be omitted, and `subject.ownershipDeclaration.*` may then also be omitted.
- **Note 3:** if none of the above shows the full ownership chain (e.g. multi-tier holding), `shareholdingStructureChart` will be requested via supplement.
- **Note 4 (US charter):** submit the charter document matching `businessType` — corporation subtypes (`B_CORPORATION` / `C_CORPORATION` / `CLOSE_CORPORATION` / `S_CORPORATION`) → `bylaws`; `LLC` → `operatingAgreement`; `LLP` / `LP` / `GENERAL_PARTNERSHIP` → `partnershipAgreement`. Only one, matching the true org form. (`operatingAgreement` also serves as the fallback when the specific charter type is unclear.)
- **Note 5 (source of funds):** mandatory. Acceptable forms include recent 6-month corporate bank statements, audited financials, key trade contracts + invoices, capital-contribution proof, or investment agreements + receipts. Multiple entries allowed (at least one). An account-balance screenshot alone is insufficient — the funds' formation chain must be shown.

**Address proof:** required when `operatingAddressSameAsRegistered = false`, or when the submitted registration documents do not state an address. Provide via the `subject.bankStatement` / `utilityBill` / `leaseAgreement` / `taxNotice` / `addressProofOther` keys; issued within the last 3 months.

### 3. Representative fields (`representative.*`)

One set per person, distinguished by the `representativeRef` property (see [Submission structure](#submission-structure)). Note: the per-person id is the `representativeRef` property of each `representatives[]` entry, **not** a `fields[]` key.

| Key | HK | US | Rules |
|-----|:--:|:--:|-------|
| `representativeRef` *(property — not a `fields[]` key)* | M | M | Stable per-person id in your system; keep unchanged across supplements. Supplied as the `representativeRef` property of each `representatives[]` entry (see [Submission structure](#submission-structure)) — do **not** place it inside `fields`. `subject.signerPersonRefId` references this value. |
| `representative.role.responsibility` | O | O | The person's responsibility relative to the company — **single value** from the enum (§[Enums](#5-enums)): `ULTIMATE_BENEFICIAL_OWNER` / `AUTHORIZED_REPRESENTATIVE` / `DIRECTOR`. |
| `representative.firstName` | M | M | English first name, ≤100. Must match the ID exactly. |
| `representative.middleName` | O | O | English middle name, ≤100. Provide if present on the ID. |
| `representative.lastName` | M | M | English last name, ≤100. Must match the ID exactly. |
| `representative.fullNameCn` | O | N/A | Chinese name, ≤50. HK: provide if the ID carries a Chinese name. |
| `representative.jobTitle` | M | M | Title (e.g. Director, CEO), ≤100. |
| `representative.birthDate` | M | M | `yyyy-MM-dd`. Must match the ID; must be ≥ 18 years old. |
| `representative.nationality` | M | M | ISO 3166-1 alpha-2. |
| `representative.ownershipPercentage` | C | C | Required when `role.responsibility = ULTIMATE_BENEFICIAL_OWNER`. `0.01`–`100`, ≤2 decimals; look-through actual percentage. |
| `representative.residentialAddress.addressLine1` | M | M | Actual residential address (not temporary), ≤200. |
| `representative.residentialAddress.addressLine2` | O | O | ≤200. |
| `representative.residentialAddress.city` | M | M | ≤100. |
| `representative.residentialAddress.state` | O | M | US mandatory (2-letter state code). |
| `representative.residentialAddress.postalCode` | O | M | US mandatory. |
| `representative.residentialAddress.countryCode` | M | M | ISO 3166-1 alpha-2. |
| `representative.email` | M | M | Required for every person, ≤128 (used for verification-code delivery). |
| `representative.phone.countryCode` | O | O | Recommended for the primary contact person. |
| `representative.phone.number` | O | O | Recommended for the primary contact person. |
| `representative.identityDocument.ssn` | N/A | M | US: personal tax id (SSN/ITIN) for every person; N/A for HK. |
| `representative.identityDocument.idType` | M | M | Enum §[Enums](#5-enums). |
| `representative.identityDocument.idNumber` | M | M | ≤64. |
| `representative.identityDocument.issuingCountry` | M | M | ISO 3166-1 alpha-2. |
| `representative.identityDocument.issueDate` | O | O | `yyyy-MM-dd`. |
| `representative.identityDocument.expiryDate` | M | M | `yyyy-MM-dd`. Long-validity IDs use `9999-12-31`. An already-expired ID fails validation. |
| `representative.ownershipAttestedAt` | C | C | ISO 8601. Required when `subject.ownershipDeclaration.hasShareholderOver25Percent` has a value. |

### 4. Representative documents (`representative.*`)

Value is a `fileId`. ID-document files are routed by `identityDocument.idType` (see the Role/ID enum below).

| Key | Req | Notes |
|-----|:--:|-------|
| `representative.passport` | C | Passport photo page (front only) — when `idType = PASSPORT`. |
| `representative.idCardFront` / `representative.idCardBack` | C | Both required for card-style IDs — see the idType routing note in §[Enums](#5-enums). |
| `representative.driversLicenseFront` / `representative.driversLicenseBack` | C | Both required when `idType = DRIVERS_LICENSE`. |
| `representative.taxIdDocument` | C | Tax-id proof (SSN / ITIN); provide together with `representative.identityDocument.ssn` for US persons. |
| `representative.proofOfAddress` | C | Required when the residential address differs from the ID's stated address. |
| `representative.photoHoldingId` | O | Requested by risk control when fraud is suspected. |
| `representative.liveSelfie` | O | As above. |
| `representative.appointmentDocument` | O | Appointment/authorization document. |
| `representative.nameChangeCertificate` | C | Required when the ID name differs from the declared name. |
| `representative.supportiveOther` | O | Other supporting materials. |

### 5. Enums

Values below are the exact accepted values. The subset actually allowed for a given channel/country is returned by the requirements flow — do not assume every value is accepted everywhere.

**`subject.country`**: `HK`, `US`.

**`subject.registrationNoType`**: `BRN` (HK), `EIN` (US).

**`subject.businessType`** (single list — not split by jurisdiction):
`B_CORPORATION`, `C_CORPORATION`, `CLOSE_CORPORATION`, `S_CORPORATION`, `LLC`, `LLP`, `LP`, `GENERAL_PARTNERSHIP`, `SOLE_PROPRIETOR`, `TRUST`, `COOPERATIVE`, `NONPROFIT_CORPORATION`, `OTHER`.

> `OTHER` requires an accompanying description. The subset offered per channel/country is returned by requirements.

**`subject.serviceAgreementType`**: `FULL` (direct service relationship), `RECIPIENT` (payee only, no direct relationship).

**`representative.role.responsibility`** (single value): `ULTIMATE_BENEFICIAL_OWNER`, `AUTHORIZED_REPRESENTATIVE`, `DIRECTOR`.

**`representative.identityDocument.idType`**: `PASSPORT`, `DRIVERS_LICENSE`, `NATIONAL_ID`, `STATE_OR_PROVINCIAL_ID`, `PERMANENT_RESIDENCY_ID`, `MATRICULATE_ID`, `MILITARY_ID`, `VISA`.

> **ID-document files by `idType`:** `PASSPORT` → `passport`; `DRIVERS_LICENSE` → `driversLicenseFront` + `driversLicenseBack`; all other government IDs (`NATIONAL_ID`, `STATE_OR_PROVINCIAL_ID`, `PERMANENT_RESIDENCY_ID`, `MATRICULATE_ID`, `MILITARY_ID`, `VISA`) → `idCardFront` + `idCardBack`.

**Address proof** (which `subject.*` document key to use): bank statement → `bankStatement`; utility bill → `utilityBill`; lease → `leaseAgreement`; tax notice → `taxNotice`; other → `addressProofOther`.

### 6. File limits

| Limit | Value |
|-------|-------|
| Max file count per submission | 30 |
| Max bytes per file | 12,582,912 (12 MB) |
| Max total bytes per submission | 104,857,600 (100 MB) |
| Allowed content types | `application/pdf`, `image/jpeg`, `image/png`, `image/heic` |

### 7. Role integrity & cross-field rules

Submission is rejected with `P_PAY_OPEN_API_INVALID_ARGUMENT` when any of the following fails:

- **Registration type matches jurisdiction:** `HK` ⇒ `registrationNoType = BRN`; `US` ⇒ `EIN`.
- **US state present:** `US` requires `subject.incorporationState`.
- **Operating address present** when `operatingAddressSameAsRegistered = false`.
- **Every representative has an `email`.**
- **Beneficial owner ownership:** when `subject.ownershipDeclaration.hasShareholderOver25Percent = true` (or an ownership document shows a ≥25% holder), at least one representative must have `role.responsibility = ULTIMATE_BENEFICIAL_OWNER`. Each such person's `ownershipPercentage` must be in `(0, 100]`, and the sum must not exceed 100.
- **ID not expired**; ID **back** file present for card-style IDs and `DRIVERS_LICENSE`.
- **Age ≥ 18** (from `birthDate`).
- **US charter document matches `businessType`** (see Note 4).
- **US personal tax id present** (`representative.identityDocument.ssn`) for every representative.
- **Required company documents present** per the matrix; source-of-funds proof present; ownership information resolvable (either an ownership document or `subject.ownershipDeclaration.*`).
- **Consents accepted:** `termsAgreed` and `dataUsageAgreed` are `true`.

---

## Deposit Endpoints

> **Precondition:** the `userId`'s platform KYB must be `APPROVED` (see [KYB Endpoints](#kyb-endpoints)). Otherwise `P_PAY_OPEN_API_INTERNAL_KYB_NOT_APPROVED` is returned.

### 1. List Deposit Accounts

```
GET /api/v2/institution/wire/deposit/accounts
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| userId | string | Yes | Sub-account UUID. |
| channel | string | Yes | Channel. |
| currency | string | No | ISO 4217. |
| page / size | integer | No | Pagination. |

**Response Fields:** `list[]` of `DepositAccount`, plus `total`.

`DepositAccount`: `{ channel, accountId, currency, status, channelStatus, instructions[], feeAmount, minDepositAmount, maxDepositAmount }`, where `status` ∈ `PENDING` (not yet remittable) / `ACTIVE` (remittable) / `UNAVAILABLE` / `CLOSED`, and each `instructions[]` element (`FundingInstruction`) carries the wire fields: `{ rails[], message, bankName, bankAddress, accountNumber, routingCode, routingCodeAlternate, swiftBic, accountHolderName, accountHolderAddress, reference, channelExtra[] }`.

### 2. List Deposit Orders

```
GET /api/v2/institution/wire/deposit/orders
```

**Request Parameters:** `userId` (required), `channel` (required), `currency`, `status`, `startTime`, `endTime`, `page`, `size`.

**Response Fields:** `list[]` of `DepositOrder`, plus `total`.

### 3. Get a Deposit Order

```
GET /api/v2/institution/wire/deposit/order
```

**Request Parameters:** `userId` (required), `orderId` (required), `channel` (required).

**Response Example:**

```json
{
  "result": true,
  "timestamp": 1785706000000,
  "data": {
    "orderId": "d-9", "channel": "bridge", "creditCurrency": "USDT",
    "receivedCurrency": "USD", "receivedAmount": "100", "feeAmount": "1",
    "creditAmount": "99", "status": "COMPLETED", "rail": "wire", "rate": "1",
    "createdAt": 1785700000000, "updatedAt": 1785700100000,
    "creditedAt": 1785700050000, "completedAt": 1785700100000
  }
}
```

`status` (`DepositOrderStatus`): `PENDING` (processing) / `CREDITED` (credited, not settled) / `COMPLETED` (final) / `FAILED` (final) / `CANCELED` (final).

On a non-success status (e.g. `FAILED`), the order also carries a `reason` object `{ code, message, retryable }`.

`createdAt` / `updatedAt` / `creditedAt` / `completedAt` are all millisecond Unix timestamps (`int64`); a lifecycle field is `0` until that event occurs (`creditedAt` before crediting, `completedAt` before the order is final).

---

## Payout Account Endpoints

> **Precondition:** the `userId`'s platform KYB must be `APPROVED` (see [KYB Endpoints](#kyb-endpoints)). Otherwise `P_PAY_OPEN_API_INTERNAL_KYB_NOT_APPROVED` is returned.

### 1. Get Payout-Account Field Requirements

Returns the required fields for a payout (payee) account, driven by channel + country + currency + rail.

```
GET /api/v2/institution/wire/payout/account/requirements
```

**Request Parameters:** `userId` (required), `channel`, `country`, `currency`, `rail`.

**Response Fields:** `{ channel, requirements[] }`, each `FieldRequirement`: `{ key, label, required, regex, isExtra, kind }`. `isExtra=true` → put the value into `channelExtra`. `kind` is `FIELD` (default) or `DOCUMENT`; a `DOCUMENT` field is supplied via `spec.documents` (upload the file first, reference by `fileId`), not as a plain value.

### 2. Create Payout Account

```
POST /api/v2/institution/wire/payout/account/create
```

**Request Body (JSON):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| userId | string | Yes | Sub-account UUID. |
| clientAccountId | string | Yes | Bind idempotency id, unique per `userId`, 1–64 chars. Retries must reuse the original value. |
| channel | string | Yes | Channel. |
| spec | object | Yes | Account spec — fields constrained by requirements. |

`spec`: `{ currency, country, rail, holderType (INDIVIDUAL|BUSINESS), accountHolderName, accountHolderAddress, bankName, routingNumber, accountNumber, accountType (CHECKING|SAVINGS), fileIds[], channelExtra[], documents[] }`. Each `documents[]` item is `{ purpose, fileId }`, where `purpose` is the requirement `key` whose `kind` is `DOCUMENT`.

**Response:** a `PayoutAccount` object (see below).

### 3. List Payout Accounts

```
GET /api/v2/institution/wire/payout/accounts
```

**Request Parameters:** `userId` (required), `channel` (required), `currency`, `page`, `size`.

**Response Fields:** `list[]` of `PayoutAccount`, plus `total`.

`PayoutAccount`: `{ accountId, channel, status, rejectReason, accountLast4, bankName, currency, country, rail, accountHolderName, createdAt, updatedAt, editableFields[] }`, where `status` ∈ `IN_REVIEW` / `AVAILABLE` / `NEEDS_UPDATE` / `UNAVAILABLE` / `DELETED`, and `rejectReason` (present on `NEEDS_UPDATE` / `UNAVAILABLE`) is an object `{ code, message, retryable }`. Use `accountId` in payout requests.

### 4. Update Payout Account

Partial update; only fields returned in `editableFields` may be changed.

```
POST /api/v2/institution/wire/payout/account/update
```

**Request Body (JSON):** `{ userId, accountId, channel, routingNumber?, accountType?, accountHolderAddress?, channelExtra?[] }` (`userId`, `accountId`, `channel` required). **Response:** a `PayoutAccount`.

### 5. Delete Payout Account

```
POST /api/v2/institution/wire/payout/account/delete
```

**Request Body (JSON):** `{ userId, accountId, channel }` (all required). **Response:** empty object.

---

## Payout Endpoints

> **Precondition:** the `userId`'s platform KYB must be `APPROVED` (see [KYB Endpoints](#kyb-endpoints)). Otherwise `P_PAY_OPEN_API_INTERNAL_KYB_NOT_APPROVED` is returned.

### 1. Create Payout (Fiat Withdrawal)

```
POST /api/v2/institution/wire/payout/order/create
```

**Request Body (JSON):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| userId | string | Yes | Sub-account UUID. |
| clientOrderId | string | Yes | Globally unique idempotency key. **Retries must reuse the original value.** |
| channel | string | No | Channel. |
| payoutAccountId | string | No | Target payout account (`accountId` from Create/List Payout Account). |
| sourceCurrency | string | No | Debit asset code (e.g. `USDT`). |
| targetCurrency | string | No | Credited asset code (e.g. `USD`). |
| amount | string | No | Total debit amount, in `sourceCurrency`. |
| channelExtra | object[] | No | Channel-specific extras. |

**Response Example:**

```json
{
  "result": true,
  "timestamp": 1785706000000,
  "data": { "orderId": "o-9", "status": "PENDING", "amount": "100", "feeAmount": "1", "finalAmount": "99" }
}
```

Response fields: `{ orderId, status, amount, feeAmount, finalAmount, reason }`; `reason` (`{ code, message, retryable }`) is present only when the channel returns one.

> **Idempotency:** always send a unique `clientOrderId`; on timeout/no-response, re-send with the **same** `clientOrderId` (or query first via [List/Get Payout Order](#2-list-payout-orders)) — never retry with a new key.

### 2. List Payout Orders

```
GET /api/v2/institution/wire/payout/orders
```

**Request Parameters:** `userId` (required), `channel` (required), `status`, `startTime`, `endTime`, `page`, `size`. **Response:** `list[]` of `PayoutOrder`, plus `total`.

### 3. Get a Payout Order

```
GET /api/v2/institution/wire/payout/order
```

**Request Parameters:** `userId` (required), `orderId` **or** `clientOrderId`, `channel` (required).

`PayoutOrder`: `{ orderId, clientOrderId, channel, payoutAccountId, sourceCurrency, targetCurrency, amount, feeAmount, finalAmount, rate, status, reason, rail, createdAt, updatedAt, completedAt, refundedAt }`, where `status` (`PayoutOrderStatus`) ∈ `PENDING` / `IN_REVIEW` / `PROCESSING` / `COMPLETED` (final) / `FAILED` (final) / `RETURNED` / `REFUNDING` / `REFUNDED`. `reason` is an object `{ code, message, retryable }` (present only when the channel returns one, e.g. on `FAILED` / `RETURNED`); `retryable` indicates whether the same order may be retried.

`createdAt` / `updatedAt` / `completedAt` / `refundedAt` are all millisecond Unix timestamps (`int64`); a lifecycle field is `0` until that event occurs (`completedAt` before the order is final, `refundedAt` before any refund).

---

## Asset (On-Chain) Endpoints

### 1. List Currencies

```
GET /api/v2/institution/asset/currencies
```

**Request Parameters:** `currency` (optional, max 60). This endpoint does not take `userId`.

**Response Fields:** `currencies[]`, each `{ currency, displayName, fullName, chainList[] }`, where each chain is `{ chain, txType, depositEnable, withdrawEnable, depositMin, withdrawMin, withdrawMax, withdrawFee, hasTag, confirm, withdrawPrecision, contractAddress, walletType, preConfirm }`.

### 2. Create On-Chain Withdrawal

The address whitelist must be enabled and the address must be whitelisted (or in the address book, for sub-accounts).

```
POST /api/v2/institution/asset/withdraw
```

**Request Body (JSON):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| userId | string | Yes | Sub-account UUID. |
| clientId | string | Yes | Idempotency key, globally unique, max 64. Retries must reuse the original value. |
| currency | string | Yes | e.g. `USDT`, max 60. |
| chain | string | Yes | A withdraw-enabled chain from *List Currencies*, max 60. |
| address | string | Yes | Destination address, max 300. |
| tag | string | Cond. | Tag/Memo, required for currencies where `hasTag=true`, max 100. |
| amount | string | Yes | Amount, max 60. |
| note | string | No | Note, max 100. |

**Response Example:**

```json
{ "result": true, "timestamp": 1785706000000, "data": { "id": "123456789", "clientId": "my-withdraw-001" } }
```

**Errors:**

| Error Code | Description |
|------------|-------------|
| `P_PAY_OPEN_API_ACCOUNT_FROZEN` | Deposits/withdrawals frozen for this account. |
| `P_PAY_OPEN_API_KYC_REQUIRED` | KYC not completed or insufficient level. |
| `P_PAY_OPEN_API_REGION_RESTRICTED` | The operation is restricted in your region. |
| `P_PAY_OPEN_API_SIGN_REJECTED` | Security signature check failed. |
| `P_PAY_OPEN_API_OPERATION_FORBIDDEN` | Blocked after high-risk behavior; `data` contains `restrict_expired_on`, `restrict_ttl`. |
| `P_PAY_OPEN_API_UNSUPPORTED_CURRENCY` | `currency` + `chain` combination unsupported. |
| `P_PAY_OPEN_API_WITHDRAW_WHITELIST_CLOSED` | Address whitelist not enabled (mandatory for Open API). |
| `P_PAY_OPEN_API_WITHDRAW_ADDRESS_NOT_WHITELISTED` | Address not on the whitelist. |
| `P_PAY_OPEN_API_WITHDRAW_ADDRESS_NOT_ALLOWED` | Address not on the configured allow list. |
| `P_PAY_OPEN_API_WITHDRAW_ADDRESS_NOT_IN_ADDRESS_BOOK` | Sub-account address not in the address book. |

### 3. Query a Single On-Chain Withdrawal

```
GET /api/v2/institution/asset/withdraw
```

**Request Parameters:** `userId` (required), and at least one of `id` (max 64) / `clientId` (max 64).

**Response:** an `AssetRecord` (see below).

### 4. Query Deposit/Withdrawal History

```
GET /api/v2/institution/asset/records
```

**Request Parameters:** `userId` (required), `type` (`DEPOSIT` / `WITHDRAW`, optional), `currency` (optional), `startTime`, `endTime`.

**Response Fields:** `records[]` of `AssetRecord`.

`AssetRecord`: `{ id, clientId, currency, chain, type (deposit|withdraw), internal, address, tag, addressFrom, tagFrom, amount, fee, status, hash, confirmations, note, approvalReason, createTime, updateTime }`.

---

## Address Book Endpoints

### 1. List Address-Book Entries

```
GET /api/v2/institution/addressBooks
```

**Request Parameters:** `userId` (required), `currency` (with `chain`), `chain` (with `currency`), `onlyWhitelist` (boolean).

**Response Fields:** `list[]` of `{ addressId, currency, chain, address, memo, label, whitelist, createTime }`, plus `total`.

### 2. Add Address-Book Entry

```
POST /api/v2/institution/addressBook
```

**Request Body (JSON):** `{ userId, currency, chain, address, label, memo? }` (`userId`, `currency`, `chain`, `address`, `label` required). **Response:** the created entry.

### 3. Delete Address-Book Entry

```
POST /api/v2/institution/addressBook/delete
```

**Request Body (JSON):** `{ userId, addressId }` (both required). **Response:** empty object.

---

## Account Endpoints

### Get Trading-Account Balances

```
GET /api/v2/institution/account/balances
```

**Request Parameters:** `userId` (required).

**Response Example:**

```json
{
  "result": true,
  "timestamp": 1785706000000,
  "data": {
    "list": [
      { "coin": "BTC", "free": "0.90000000", "frozen": "0.00000000" },
      { "coin": "USDT", "free": "100.00000000", "frozen": "900.00000000" }
    ]
  }
}
```

`list[]`: `{ coin, free, frozen }` (8-decimal decimal strings), sorted by coin ascending.

---

## Convert Endpoints

### 1. Create Conversion

```
POST /api/v2/institution/convert/order/create
```

**Request Body (JSON):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| userId | string | Yes | Sub-account UUID. |
| baseCoin | string | Yes | Base currency. |
| quoteCoin | string | Yes | Quote currency. |
| side | string | Yes | `BUY` / `SELL`. |
| baseAmount | string | Cond. | Base amount — required only when `side=SELL`. |
| quoteAmount | string | Cond. | Quote amount — required only when `side=BUY`. |

**Response Example:**

```json
{ "result": true, "timestamp": 1785706000000, "data": { "orderId": "ord-1" } }
```

**Errors:**

| Error Code | Description |
|------------|-------------|
| `P_PAY_OPEN_API_CONVERT_INVALID_AMOUNT` | `side=SELL` without `baseAmount`, or `side=BUY` without `quoteAmount`. |
| `P_PAY_OPEN_API_SYMBOL_MAINTENANCE` | Trading pair under maintenance. |
| `P_PAY_OPEN_API_SYMBOL_MARKET_CLOSE` | Trading pair closed (non-trading day). |

### 2. List Conversion Orders

```
GET /api/v2/institution/convert/orders
```

**Request Parameters:** `userId` (required), `startTime`, `endTime`. **Response:** `list[]` of `ConvertRecord`.

### 3. Get a Conversion Order

```
GET /api/v2/institution/convert/order
```

**Request Parameters:** `userId` (required), `orderId` (required).

`ConvertRecord`: `{ orderId, baseCoin, quoteCoin, baseAmount, quoteAmount, side, price, status, failReason, createTime, updateTime }`.

---

## File Endpoints

Files (KYB / supporting documents) are uploaded first and referenced elsewhere by `fileId`.

### 1. Upload File

```
POST /api/v2/institution/file/upload
```

**Request Parameters:** `userId` (required, in the query string — the request body is multipart, so `userId` cannot go in the body here).

**Request Body (multipart/form-data):** `file` (binary, required).

**Response Example:**

```json
{ "result": true, "timestamp": 1785706000000, "data": { "fileId": "..." } }
```

### 2. Download File

```
GET /api/v2/institution/file/download
```

**Request Parameters:** `userId` (required), `fileId` (string, required). **Response:** binary stream (`application/octet-stream`).
