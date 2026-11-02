# ICT381 End-of-Course Assessment — July Semester 2026
## Software Engineering and DevOps

| | |
|---|---|
| **Name** | Lau Xing Yao |
| **SUSS PI No.** | B2411711 |
| **Course** | ICT381 Software Engineering and DevOps |
| **Submission date** | 08 November 2026 |
| **Repository** | https://github.com/ICT381/ict381-2026-t02-eca-xxingyao |

### Repository layout

```
/
├── frontend/              React application
├── backend/               Flask API + tests
├── infra/
│   ├── terraform/         Infrastructure as code (Q2)
│   ├── ansible/           Deploy playbooks (Q3b)
│   └── local-ansible/     CI host bootstrap (Q3a)
├── Jenkinsfile            Multibranch pipeline (Q4)
├── evidence/              Run logs and screenshots, by question
└── README.md              This file
```

### Marker's index

| Question | Topic | Marks | Evidence section |
|---|---|---|---|
| 1 | Monorepo migration | 5 | [Q1](#question-1--monorepo-migration) |
| 2a | Terraform authoring | 13 | [Q2a](#question-2a--work-out-and-author-the-terraform) |
| 2b | Terraform run evidence | 6 | [Q2b](#question-2b--run-it-and-capture-the-evidence) |
| 2c | Reflection: current → target | 6 | [Q2c](#question-2c--reflection-current-to-target) |
| 3a | Bootstrap the CI host | 8 | [Q3a](#question-3a--bootstrap-the-ci-host) |
| 3b | Deploy playbooks | 13 | [Q3b](#question-3b--fill-in-and-run-the-two-deploy-playbooks) |
| 3c | Idempotency | 4 | [Q3c](#question-3c--idempotency) |
| 4a | The test gate | 7 | [Q4a](#question-4a--the-test-gate) |
| 4b | Build the release pipeline | 14 | [Q4b](#question-4b--build-the-release-pipeline) |
| 4c | Activate and run the pipeline | 4 | [Q4c](#question-4c--activate-and-run-the-pipeline) |
| 4d | Reflection: the test gate | 3 | [Q4d](#question-4d--reflection) |
| 5 | Operate: reasoning about rollback | 8 | [Q5](#question-5--operate-reasoning-about-rollback) |
| 6 | Reflection: what the monorepo resolved | 9 | [Q6](#question-6--what-the-monorepo-resolved) |

---

# Question 1 — Monorepo migration

**(5 marks)**

### 1. The migrated monorepo

The three codebases were relocated into a single repository:

| Was | Now |
|---|---|
| `myReactApp` (separate repo) | `/frontend` |
| `StaycationX` (separate repo) | `/backend` |
| `automation` (separate repo) | `/infra` |

### 2. Pull request

**PR URL:** `https://github.com/ICT381/ict381-2026-t02-eca-xxingyao/pull/2`

The PR diff is the before/after for items 3 and 4 below.

### 3. Jenkinsfile before/after

Three separate checkouts collapsed into a single monorepo checkout, and stage commands repointed to `/infra`.

| Stage | Before | After |
|---|---|---|
| Checkout | 3 × `git` clone (automation, StaycationX, myReactApp) | `checkout scm` |
| Docker | `ansible-playbook ansible/build-docker.yaml` | `ansible-playbook infra/ansible/build-docker.yaml` |
| Terraform | `terraform -chdir=terraform ...` | `terraform -chdir=infra/terraform ...` |
| Ansible | `ansible-playbook ... ansible/prod-application.yaml` | `ansible-playbook ... infra/ansible/prod-application.yaml` |

### 4. Ansible playbook before/after

| File | Line | Before | After |
|---|---|---|---|
| `infra/ansible/build-docker.yaml` | 35 | `project_src: /opt/StaycationX` | `project_src: /opt/backend` |
| `infra/ansible/build-docker.yaml` | 65 | build context `.../StaycationX/` | build context `.../backend/` (backend image) |
| `infra/ansible/build-docker.yaml` | 79 | build context `.../StaycationX/` | build context `.../backend/` (MongoDB image) |
| `infra/ansible/build-docker.yaml` | 94 | build context `.../myReactApp/` | build context `.../frontend/` |
| `infra/ansible/prod-application.yaml` | 39 | `src: .../StaycationX/dockerhub.yml` | `src: .../backend/dockerhub.yml` |

---

# Question 2 — Infrastructure as code with Terraform

## Question 2a — Work out and author the Terraform

**(13 marks)**

All resources are in [`infra/terraform/main.tf`](infra/terraform/main.tf); the outputs are in [`infra/terraform/output.tf`](infra/terraform/output.tf).

### 1. Committed Terraform configuration

| Resource | File / line | Notes |
|---|---|---|
| CI EC2 instance | `main.tf`, line 152 | `aws_instance.jenkins`, group `jenkins`, `ci_sg` |
| Application EC2 instance | `main.tf`, line 169 | `aws_instance.app`, group `web`, `application_sg` |
| Database EC2 instance | `main.tf`, line 186 | `aws_instance.db`, `database_sg`, no Elastic IP. The default subnet gives it a public IPv4 for outbound traffic only (ECR pulls, apt); inbound is limited by `database_sg` |
| Elastic IP — CI host | `main.tf`, line 206 | `aws_eip.jenkins_eip` |
| Elastic IP — application host | `main.tf`, line 211 | `aws_eip.app_eip` |
| S3 static-website bucket | `main.tf`, line 221 | `awscc_s3_bucket.site` (see note below). Website config line 225, public-access block line 237, public-read policy line 245 |
| ECR repository — backend | `main.tf`, line 263 | `ict381_backend` |
| ECR repository — MongoDB | `main.tf`, line 269 | `ict381_mongo` |

**Why the bucket uses `awscc_s3_bucket`.** The `aws_s3_bucket` resource reads the bucket's Object Lock configuration (`s3:GetBucketObjectLockConfiguration`) after creating it, and the AWS Academy Learner Lab denies that read through a service control policy. The bucket is therefore created with `awscc_s3_bucket` from the `hashicorp/awscc` provider; its website configuration, public-access block and public-read policy are ordinary `aws` provider resources.

### 2. Remote-state backend

S3 backend with `use_lockfile` (Terraform ≥ 1.10), not local state.

- **File:** `main.tf`, lines 1–19 (`backend "s3"` at line 13, `use_lockfile = true` at line 17)
- **State bucket:** `ict381-eca-tfstate-xxingyao-203635632743-us-east-1-an` (created in the AWS Console before `terraform init`)

### 3. Security-group rules enforcing the boundaries

| Boundary | Rule | File / line |
|---|---|---|
| MongoDB 27017 from application SG only | `from_port 27017`, source `application_sg` | `main.tf`, lines 125 and 128 |
| SSH to application host from CI SG only | `from_port 22`, source `ci_sg` | `main.tf`, lines 103 and 106 |
| SSH to database host from CI SG only | `from_port 22`, source `ci_sg` | `main.tf`, lines 132 and 135 |
| Jenkins 8080 from GitHub webhook ranges only | GitHub `hooks` ranges from `api.github.com/meta` | `main.tf`, line 62; IPv4 lines 65–73, IPv6 lines 74–77 |
| Backend API 5000 inbound from internet | `from_port 5000`, `0.0.0.0/0` | `main.tf`, lines 96 and 99 |

The old shared security group (22, 80, 5000, 27017, 8080, 9000 and 3000 open to `0.0.0.0/0`) was removed.

### 4. IAM instance-profile attachments

`iam_instance_profile = "LabInstanceProfile"` on all three hosts — the CI host pushes to S3/ECR through it, and the application and database hosts pull from the private ECR through it.

| Host | File / line |
|---|---|
| CI | `main.tf`, line 157 |
| Application | `main.tf`, line 174 |
| Database | `main.tf`, line 191 |

## Question 2b — Run it and capture the evidence

**(6 marks)**

### 1. Terraform apply output

**Log:** [`evidence/q2b-apply.log`](evidence/q2b-apply.log)

Covers the CI, application and database instances, the Elastic IPs, the S3 website bucket, the private ECR repositories, and the security groups.

### 2. S3 bucket serving the static site

**Screenshot:** [`evidence/q2b-s3-site.png`](evidence/q2b-s3-site.png)

![Placeholder page served from the S3 website endpoint](evidence/q2b-s3-site.png)

### 3. Terraform output values

**Log:** [`evidence/q2b-output.log`](evidence/q2b-output.log)

| Output | Value | Used by |
|---|---|---|
| `site_website_endpoint` | `ict381-eca-site-xxingyao-203635632743.s3-website-us-east-1.amazonaws.com` | The public site URL |
| `ci_public_ip` | `52.54.76.84` | Q3a SSH, Q4 webhook target |
| `app_public_dns` | `ec2-3-214-100-242.compute-1.amazonaws.com` | Frontend API endpoint |
| `app_private_dns` | `ip-172-31-42-96.ec2.internal` | Ansible/SSH deploy target |
| `site_bucket_name` | `ict381-eca-site-xxingyao-203635632743` | Q4 `aws s3 sync` target |
| `backend_ecr_url` | `203635632743.dkr.ecr.us-east-1.amazonaws.com/ict381_backend` | Q3b/Q4 image pushes |
| `mongo_ecr_url` | `203635632743.dkr.ecr.us-east-1.amazonaws.com/ict381_mongo` | Q3b/Q4 image pushes |
| `db_private_ip` | `172.31.40.21` | Ansible target + backend Mongo endpoint |

## Question 2c — Reflection: current to target

**(6 marks)**

Before = `automation/terraform/` as migrated in Q1 (commit `621a3ef`). After = [`infra/terraform/main.tf`](infra/terraform/main.tf).

### Difference 1 — Two applies and two local states → one config, one remote state

| | |
|---|---|
| **Before** | The same `main.tf` was applied twice: once from my machine for the CI host (Lab 5A), then again by the Jenkins pipeline for the production host (`Jenkinsfile` line 42, `-var="name=prod-ict381" -var="group=web"`). There was no backend block, so each run kept its own local `terraform.tfstate` (one on my machine, one in the Jenkins workspace). |
| **After** | One `main.tf` declares every tier (CI, application, database, S3, ECR) and stores one state in S3 with locking (`backend "s3"` line 13, `use_lockfile = true` line 17). A single `terraform apply` built all 14 resources ([`q2b-apply.log`](evidence/q2b-apply.log)). |
| **Value added** | Reliability, maintainability |
| **Why this is an improvement** | There is one source of truth. Two state files each saw only half the estate, so one run could not see or safely change the other's resources. The state now survives losing my laptop or the Jenkins workspace, the lock file stops two applies from writing the state at the same time, and one plan shows the effect of a change on the whole topology. |

### Difference 2 — Shared wide-open security group → per-tier least-privilege groups

| | |
|---|---|
| **Before** | One group, `jenkins-sg` (old `main.tf` line 26), opened 5000, 22, 80, 27017, 8080, 9000 and 3000 to `var.source_ip_block`, which defaulted to `0.0.0.0/0` (old `variables.tf` line 3). It was attached to both the CI and production hosts. |
| **After** | `ci_sg` (line 51): 22 from anywhere, 8080 from GitHub's webhook ranges only. `application_sg` (line 92): 5000 from the internet, 22 from `ci_sg` only. `database_sg` (line 121): 27017 from `application_sg` only, 22 from `ci_sg` only. Ports 80, 3000 and 9000 are no longer open anywhere. |
| **Value added** | Security |
| **Why this is an improvement** | MongoDB and Jenkins are no longer reachable from the whole internet, and each host opens only the ports its role needs. Rules that reference another group's ID follow group membership rather than IP addresses, so they keep working when instances are replaced. A compromised host no longer has network access to every port on every other host. |

### Difference 3 — 3-in-1 production host → each tier on its own host

| | |
|---|---|
| **Before** | One production EC2 ran the backend (5000), MongoDB (27017) and an nginx container serving React (80) together, deployed with `docker compose` and `dockerhub.yml` (`infra/ansible/prod-application.yaml` lines 37–61). |
| **After** | `aws_instance.app` (line 169) runs only the backend, `aws_instance.db` (line 186) runs only MongoDB, and the frontend is served from S3. The CI host stays separate. |
| **Value added** | Reliability, scalability, security |
| **Why this is an improvement** | A problem in one tier (for example MongoDB using all the memory) can no longer take down the others on the same machine. Each tier can be resized or scaled on its own. Splitting the hosts is also what makes Difference 2 possible: the database can only be limited to "the application host" when it is a separate host. |

### Difference 4 — nginx container for the frontend → S3 static website

| | |
|---|---|
| **Before** | The built React app was served by an nginx container on the production host, on port 80. |
| **After** | An S3 bucket (`awscc_s3_bucket.site`, line 221) with website hosting (line 225, `index.html` as both index and error document) and a public-read policy (line 245). Q4 deploys the build with `aws s3 sync`. |
| **Value added** | Scalability, reliability, maintainability |
| **Why this is an improvement** | S3 serves static files without a server to patch, size or keep running, and it handles load without changes. Frontend releases no longer touch the backend host, and port 80 is no longer needed on any security group. |

### Difference 5 — Docker Hub with stored credentials → private ECR with instance-profile access

| | |
|---|---|
| **Before** | Images were pushed to Docker Hub using a username and password stored in Jenkins (`docker-hub-credentials`, `Jenkinsfile` lines 22–24). |
| **After** | Two private repositories, `ict381_backend` (line 263) and `ict381_mongo` (line 269). The CI, application and database hosts authenticate through `LabInstanceProfile`. |
| **Value added** | Security, maintainability |
| **Why this is an improvement** | No long-lived registry password has to be stored or rotated in Jenkins. Access is controlled by the IAM role attached to each host, and the images are private instead of on a public registry. |

# Question 3 — Automation with Ansible

## Question 3a — Bootstrap the CI host

**(8 marks)**

### (a)(i) Major changes from the base `automation/local-ansible/`

> Compare the provided `infra/local-ansible/` against the base `automation/local-ansible/`. Identify the major changes and explain why each was made: what was removed, what was added, and which files were deleted or renamed.

The provided folder was copied over `infra/local-ansible/`; the commit's diff of that folder shows every change below.

**Files at a glance**

| Base `automation/local-ansible/` | Provided `infra/local-ansible/` | Type |
|---|---|---|
| `application1.yaml` | — | Deleted |
| `gen-gpgkey-ubuntu.yaml` | — | Deleted |
| `application2.yaml` | `jenkins.yaml` | Renamed and rewritten |
| `common.yaml` | `common.yaml` | Modified (cut down) |
| `ansible.cfg`, `inventory` | `ansible.cfg`, `inventory` | Modified |

**What changed and why**

| Change | Type | What changed | Why |
|---|---|---|---|
| App build and deploy on the CI host | Deleted (`application1.yaml`) | Cloned `StaycationX` and `myReactApp` onto the CI host with deploy keys, built the images, pushed them to Docker Hub, and ran the whole app there with `docker compose` and `dockerhub.yml`. | The CI host must not host the application or the database. Images now go to private ECR (Q3b `build-docker.yaml`) and are deployed to the separate application and database hosts by `infra/ansible/`. One monorepo also replaces the two separate repos. |
| GPG key and `pass` credential store | Deleted (`gen-gpgkey-ubuntu.yaml`) | Generated a GPG key and set up `pass` so Docker could store the Docker Hub password. | Docker Hub is replaced by ECR, which the CI host reaches through `LabInstanceProfile`. With no registry password to store, the credential store, `pass`, `rng-tools`, the credential helper and the `juju4.gpgkey_generate` role are all removed. |
| Secrets and GitHub deploy keys | Removed (`common.yaml`) | Loading `GITHUB_PAT` and the Docker Hub login from `secrets.yaml`, generating a deploy key per repo, and uploading them to GitHub. | There's no Docker Hub login and one monorepo. In Q3b the CI host clones it over HTTPS with a read-only fine-grained token, so no secrets file or deploy keys are needed. |
| Terraform on the CI host | Removed (`application2.yaml` → `jenkins.yaml`) | The HashiCorp repository and the `terraform` install. | Terraform now runs once, locally, from one config (Q2). The pipeline no longer provisions infrastructure. |
| AWS CLI v2 | Added (`common.yaml`) | Downloads and installs AWS CLI v2, each step guarded with `creates:`. | The CI host needs `aws` for ECR login and `aws ecr list-images` (Q3b) and `aws s3 sync` (Q4). The guards make reruns skip these steps. |
| Docker install and docker groups | Changed / added (`common.yaml`, `jenkins.yaml`) | Installs `docker-ce`, `docker-ce-cli`, `containerd.io` and `docker-compose-plugin` with `state: present` (was `docker-ce` with `state: latest`). Adds both `ubuntu` and `jenkins` to the `docker` group. | The compose plugin is needed for `docker compose` (Q4 test harness). `ubuntu` runs Docker in the Q3b build and `jenkins` runs it in the Q4 pipeline, without `sudo`. `state: present` doesn't upgrade on every rerun. |
| SSH key on the CI host | Added (`common.yaml`, `jenkins.yaml`) | Copies `labsuser.pem` to `/home/ubuntu` and `/var/lib/jenkins`, each owned by that user, mode `0400`. | The application and database hosts only accept SSH from the CI host, so Ansible deploys from there: `ubuntu` for the manual Q3b run, `jenkins` for the Q4 pipeline. |
| Guarded reboot | Changed (`jenkins.yaml`) | Base rebooted on every run. Now it only reboots `when:` the `jenkins` docker-group change actually happened. | The reboot is only needed once. Guarding it, together with `state: present` and the `creates:` guards, keeps a second run at `changed=0` (Q3c idempotency). |
| Connection settings | Changed (`ansible.cfg`, `inventory`) | Added `host_key_checking = False` and pinned `interpreter_python = /usr/bin/python3`. The inventory now names the host directly: `ci ansible_host=<Elastic IP> ansible_user=ubuntu`. | The CI host can be rebuilt, which changes its SSH host key and would otherwise block the bootstrap. Its Elastic IP from Q2 is stable, so the inventory can point at it directly. |

### (a) Bootstrap run

**Log:** [`evidence/q3a-bootstrap.log`](evidence/q3a-bootstrap.log) — `ansible-playbook common.yaml jenkins.yaml`

Both plays finished with `failed=0` (final `PLAY RECAP`: `ci : ok=20 changed=17 unreachable=0 failed=0`).

### (a) Bootstrap proof

**Log:** [`evidence/q3a-verify.log`](evidence/q3a-verify.log)

| Check | Result |
|---|---|
| Docker version | `Docker version 29.9.2, build a82e528` |
| Ansible version | `ansible [core 2.21.5]` |
| AWS CLI version | `aws-cli/2.39.3` |
| `labsuser.pem` present on host | `-r-------- 1 ubuntu ubuntu 1674 … /home/ubuntu/labsuser.pem` |
| Jenkins on 8080 (`X-Jenkins` header) | `HTTP/1.1 403 Forbidden` with `X-Jenkins: 2.580.2` (403 is expected before login) |

The Jenkins check uses `curl -sI http://localhost:8080 | grep -iE "^HTTP|^X-Jenkins"` instead of `| head -5`, because Jenkins sends the `X-Jenkins` header after its security headers, outside the first five lines.

## Question 3b — Fill in and run the two deploy playbooks

**(13 marks)**

### (b) Completed files

| File | What was filled in |
|---|---|
| [`infra/ansible/build-docker.yaml`](infra/ansible/build-docker.yaml) | Build-and-push tasks in the `YOUR SCRIPT` block: build and push the backend image, then build the MongoDB image from `backend/DockerfileMongo` and push it, each tagged `{{ image_tag }}` (default `latest`) |
| [`infra/ansible/inventory.ini`](infra/ansible/inventory.ini) | `[app]` → `ip-172-31-42-96.ec2.internal`, `[db]` → `172.31.40.21`, and the backend and MongoDB ECR repository URLs, all from the Q2 `terraform output` |
| [`infra/ansible/prod-application.yaml`](infra/ansible/prod-application.yaml) | MongoDB play → `hosts: db`, backend play → `hosts: app`, and `image_tag: latest` as the default |

`ansible.cfg` and the two compose templates under `templates/` are unchanged from the provided files.

**Backend files the build needs.** This repo uses my SkipQ TMA backend, which had no Dockerfiles, so `build-docker.yaml` had nothing to build from `backend/`. I added:

| File | Why |
|---|---|
| [`backend/Dockerfile`](backend/Dockerfile) (new) | Builds the API image (`python:3.12-slim`, `gunicorn` on port 5000) and sets `MONGODB_HOST=db` so the backend uses the `db` name mapped by `extra_hosts` |
| [`backend/DockerfileMongo`](backend/DockerfileMongo), [`backend/db_seed_restore.sh`](backend/db_seed_restore.sh) | The provided files, unchanged |
| [`backend/db_seed/skipq/`](backend/db_seed/skipq) | A `mongodump` of the database produced by my existing `db_seed/seed.py`, in the dump format `mongorestore --drop /opt` expects |

### (b) Run logs

| Log | What it proves |
|---|---|
| [`evidence/q3b-build-push.log`](evidence/q3b-build-push.log) | Both images built and pushed to private ECR (`changed=4 failed=0`) |
| [`evidence/q3b-ecr-images.log`](evidence/q3b-ecr-images.log) | `aws ecr list-images` lists the pushed image in both `ict381_backend` and `ict381_mongo` |
| [`evidence/q3b-deploy.log`](evidence/q3b-deploy.log) | The split deploy ran across both hosts (`application` and `database`: `changed=9 failed=0`) |

### (b) Service verification

**Log:** [`evidence/q3b-verify.log`](evidence/q3b-verify.log)

The verification commands are the paper's, adapted to my database name (`skipq` instead of `staycation`).

| Check | Expected | Result |
|---|---|---|
| `docker ps` on database host | MongoDB container running | `mongo-db-1` running `ict381_mongo:latest`, port 27017 |
| `appUsers` count | Greater than 0 — proves first-start seeding | `appUsers count: 5` (3 vendors, 2 diners) |
| `docker ps` on application host | Backend container running | `backend-backend-1` running `ict381_backend:latest`, port 5000 |
| Backend `extra_hosts` mapping | `db` → database host private address | `[db:172.31.40.21]` |
| Backend log | Started cleanly | `gunicorn` listening at `http://0.0.0.0:5000`, worker booted, no errors |
| `curl` application host :5000 | Any HTTP response | `HTTP/1.1 404 NOT FOUND` with the app's own `{"error":"No such endpoint"}` (no route at `/`) |
| Login `curl` (additional proof) | Backend reads `appUsers` across hosts | `HTTP/1.1 200 OK` with a token for `Tan Wei Ling`, role `Diner` |

The extra login check is there because my backend connects to MongoDB on the first request, not at start-up, so its log alone cannot show the connection.

### (b) Question 1 — Why does the backend container need the `db` `extra_hosts` mapping?

> Why does the backend need this in the split deployment, when the original co-located `dockerhub.yml` did not?

**How my backend finds MongoDB.** `app/__init__.py` loads `Config` from `app/config.py`, which reads the host from the `MONGODB_HOST` environment variable (default `127.0.0.1`). It is not tied to `FLASK_ENV=development`: it can be set in any environment. My `backend/Dockerfile` sets `MONGODB_HOST=db`, so the container always looks for a host called `db`.

**How the old single-host setup resolved `db`.** In the co-located `dockerhub.yml`, the backend, MongoDB and Nginx were services in one Docker Compose project on one host. Compose puts them on a shared network with built-in DNS, so the service name `db` resolved to the MongoDB container automatically.

**What changed.** MongoDB now runs in a separate Compose project on a separate EC2 host. The backend's project on the application host has no `db` service, so Docker's DNS cannot resolve the name and the connection would fail. `extra_hosts` in `templates/backend-compose.yml.j2` adds `db → 172.31.40.21` (the database host's private address, from the inventory) to the container's `/etc/hosts`. The verify log confirms it: `[db:172.31.40.21]`. The backend then connects over the private network, which is what `database_sg` allows (27017 from `application_sg` only), with no code change.

### (b) Question 2 — Why is the AWS CLI installed on the application and database hosts?

The setup play in `prod-application.yaml` installs the AWS CLI so each host can run `aws ecr get-login-password | docker login` against the private ECR registry (the "Authenticate Docker to the private ECR" task). The CLI gets a temporary token from `LabInstanceProfile`, so no password is stored anywhere.

It must be on those two hosts because they are the ones that pull the images: `docker compose` on the database host pulls `ict381_mongo`, and on the application host it pulls `ict381_backend`. A `docker login` is per host. The CI host's login does not carry over, and because the repositories are private, a host that has not logged in cannot pull.

### (b) Question 3 — What each verification command checks

| Command | What it checks | Why it matters for confirming the split deploy |
|---|---|---|
| `docker ps` (database host) | The MongoDB container from `ict381_mongo:latest` is up | Proves the database tier was pulled from ECR and is running on its own host |
| `mongosh` appUsers count | The `skipq` database has user accounts (5) | Proves the image seeded itself on first start from the baked-in dump, so logins will work |
| `docker ps` (application host) | The backend container from `ict381_backend:latest` is up on 5000 | Proves the backend tier was pulled from ECR and is running on a separate host from MongoDB |
| `docker inspect` extra_hosts | `db` maps to `172.31.40.21` | Proves the name the backend uses points at the database host's private address — the link between the two hosts |
| `docker logs` backend | `gunicorn` started and is listening on `0.0.0.0:5000` without errors | Proves the backend process is healthy, not crash-looping |
| `curl` :5000 | The API answers from outside the host (404 from the app itself) | Proves port 5000 is open in `application_sg` and the backend is serving, which is how the browser will reach it |

## Question 3c — Idempotency

**(4 marks)**

### (c) Idempotency log

**Log:** [`evidence/q3c-idempotency.log`](evidence/q3c-idempotency.log)

`PLAY RECAP` reports `changed=0` on the second run.

```
TODO — paste the PLAY RECAP line here
```

### (c) Why the idempotent deploy matters

`TODO — ground in: how often Q4's pipeline runs prod-application.yaml (every merge to main); what would happen each run if re-deploying tore down and rebuilt even when nothing changed; what Q5's rollback does with this same playbook.`

---

# Question 4 — Continuous integration and delivery

## Question 4a — The test gate

**(7 marks)**

### (a)(i) Completed test harness

**File:** `backend/test-compose.yml` — every `REPLACE_WITH_...` placeholder resolved.

| Service | Purpose | Key configuration |
|---|---|---|
| `TODO` (db) | Seeded MongoDB from `DockerfileMongo` | Service name matches the Mongo host `create_app()` uses by default |
| `test` | `python:3.12`, backend source mounted | Runs `pip install -r requirements.txt && python -m pytest -vv tests/unit tests/functional` |

### (a)(ii) Both suites run

| Log | Suite |
|---|---|
| [`evidence/q4a-frontend.log`](evidence/q4a-frontend.log) | React suite in `node:16.20.2-alpine` |
| [`evidence/q4a-backend.log`](evidence/q4a-backend.log) | `tests/unit` + `tests/functional` against seeded Mongo |

A failing test here is expected and intentional — the red → green transition is demonstrated in part (c).

### (a) Question 1 — Why does the backend test run need a MongoDB at all?

`TODO`

### (a) Question 2 — Why does the test gate need the database seeded with the staycation data?

`TODO`

### (a) Question 3 — One improvement to the backend testing in this gate

`TODO — ground it in this build, not generic testing advice.`

## Question 4b — Build the release pipeline

**(14 marks)**

### (b) The completed pipeline file

**File:** `Jenkinsfile` — every `REPLACE_WITH_` filled.

| Blank | What it achieves | Value used |
|---|---|---|
| `SITE_BUCKET` | Q2 output — S3 sync target | `TODO` |
| `APP_PUBLIC_DNS` | Q2 output — frontend API base | `TODO` |
| Tag release | `git tag ${RELEASE_TAG}` + push, wrapped in `sshagent(['github-ssh-key'])` | `TODO` |
| Deploy frontend to S3 | `aws s3 sync … --delete --region ${AWS_REGION}` | `TODO` |
| Deploy backend | Build + push `:vN` to ECR, then Ansible with `-e image_tag=${RELEASE_TAG} -e mongo_image_tag=${RELEASE_TAG}` | `TODO` |
| `main`-only guards | `when { branch 'main' }` on the three deploy stages | `TODO` |

### (b) The frontend API base

`REACT_APP_API_URL` change applied across five files:

- [ ] `frontend/src/Components/Form/form.js`
- [ ] `frontend/src/Pages/show.js`
- [ ] `frontend/src/Pages/manage.js`
- [ ] `frontend/src/Pages/explore.js`
- [ ] `frontend/src/Pages/book.js`

### (b) Local development still works

**Screenshot:** `TODO — evidence/q4b-local-dev-network.png`

Shows `npm start` on :3000 loading data from the local `docker compose` backend on `localhost:5000`.

### (b) Write-up 1 — The local-development fix

> The replacement line works for the deployed build but breaks local development. Modify the change so local dev still works while still using the injected value for the deployed build, and explain the approach.

`TODO — state the approach and why it works for both cases.`

### (b) Write-up 2 — The frontend build command explained

```
docker run --rm -e REACT_APP_API_URL=http://${APP_PUBLIC_DNS}:5000 \
  -v "$PWD:/app" -w /app node:16.20.2-alpine sh -c "npm ci && npm run build"
```

| Part | What it does | Why |
|---|---|---|
| `docker run --rm` | `TODO` | `TODO` |
| `-e REACT_APP_API_URL=…` | `TODO` | `TODO` |
| `-v "$PWD:/app"` | `TODO` | `TODO` |
| `-w /app` | `TODO` | `TODO` |
| `node:16.20.2-alpine` | `TODO` | `TODO` |
| `npm ci` | `TODO` | `TODO` |
| `npm run build` | `TODO` | `TODO` |

### (b) Write-up 3 — Why the `main`-only guard is on the deploy stages only

`TODO — why Checkout and the two test stages are deliberately unguarded.`

## Question 4c — Activate and run the pipeline

**(4 marks)**

### (c) The tagged release

**Screenshot:** `TODO — evidence/q4c-github-tags.png`

Release tag pushed: `TODO — vN`

### (c) The live site, logged in end to end

**Screenshot:** `TODO — evidence/q4c-live-site-login.png`

Single screenshot showing all three:
- [ ] Browser address bar with the S3 website URL
- [ ] The "Log In" heading (the Q4 UI change — proves this is *this* pipeline's release, not the Q3b deploy)
- [ ] Network tab: login request to `http://<application_host_public_dns>:5000/...` at **status 200**

### (c) Webhook

**Screenshot:** `TODO — evidence/q4c-webhook.png`

Webhook at `http://<ci_host_public_address>:8080/github-webhook/`, subscribed to Pushes and Pull requests, with a 200 in Recent Deliveries.

### (c) The pipeline stood up

| Screenshot | Shows |
|---|---|
| `TODO — evidence/q4c-job-config.png` | Multibranch job configuration |
| `TODO — evidence/q4c-credentials.png` | `github-ssh-key` and the fine-grained GitHub token |

### (c) The gate is causal — red → green → merge → deploy

| Step | Evidence | Screenshot |
|---|---|---|
| 1. Push with failing test → red build, PR ✗ | `TODO` | `TODO` |
| 2. Fix in a second commit → green, PR ✓ | `TODO` | `TODO` |
| 3. Merge after the green check | `TODO` | `TODO` |
| 4. Gate re-runs on `main`, then deploy stages run | `TODO` | `TODO` |

No red pull request was merged at any point.

### (c) Why the SSH-tunnelled Jenkins access is secure

> You reach the Jenkins UI over an SSH tunnel instead of opening port 8080 to the internet. What makes this access path secure — what protects it, and which attack surface does it remove?

`TODO`

## Question 4d — Reflection

**(3 marks)**

### (d)(a) Against change-scoped testing

> A teammate argues the gate is wasteful: when a PR touches only `/frontend`, run the React suite alone; when it touches only `/backend`, run the backend suite alone. Counter this.

`TODO — give the context and the reasons for running both suites, grounded in this build.`

### (d)(b) Against testing once

> The gate runs the whole suite on every feature-branch push, then again on the `main` build before the deploy stages. Explain why the second run is not redundant.

`TODO`

---

# Question 5 — Operate: reasoning about rollback

**(8 marks)**

> Every mechanism relied on must quote the exact names and values from this repository — the actual identifiers, outputs, commands and files produced in Questions 1–4 — and cite where each is defined.

### Reference: artifacts this rollback relies on

| Artifact | Exact value | Defined in |
|---|---|---|
| Release tag format | `TODO` | `TODO` |
| Backend ECR repository | `TODO` | `TODO` |
| MongoDB ECR repository | `TODO` | `TODO` |
| Site S3 bucket | `TODO` | `TODO` |
| Deploy playbook | `infra/ansible/prod-application.yaml` | `TODO` |
| Image tag parameters | `-e image_tag=` / `-e mongo_image_tag=` | `TODO` |

### (a) Returning each tier to a previous stable version

`TODO — for both frontend and backend: what you check out, rebuild or redeploy, and which Q1–4 artifacts you rely on. Identify where a tier can be restored WITHOUT rebuilding, and explain why that is possible.`

### (b) Keeping the two tiers consistent

`TODO — how you ensure frontend and backend return to the same release together. What property of the way they were built and released guarantees this?`

### (c) Database deployment handling

`TODO — issues with redeploying the database on every release, plus an improvement, grounded in how DockerfileMongo / db_seed_restore.sh seed and prod-application.yaml actually behave.`

### (d) Why the infrastructure stays untouched

`TODO — what separates "what runs" from "what it runs on", and why that separation makes rollback a fast redeploy rather than a rebuild.`

### (e) Detecting it sooner, recovering faster

`TODO — how you would notice the failure faster, shorten recovery, or prevent recurrence.`

---

# Question 6 — What the monorepo resolved

**(9 marks)**

> At least three distinct points. Each must be grounded in concrete cross-repository coordination friction encountered in the TMA (where frontend and backend were separate repos) and linked to a specific artifact from Questions 2–5 that demonstrates how a single repository removed that friction. Make the causal relationship clear.

### Point 1 — `TODO: title`

| | |
|---|---|
| **TMA friction** | `TODO — the concrete coordination problem encountered` |
| **Artifact from Q2–5** | `TODO — the specific file, log or output` |
| **Why the restructuring eliminates it** | `TODO — the causal explanation` |

### Point 2 — `TODO: title`

| | |
|---|---|
| **TMA friction** | `TODO` |
| **Artifact from Q2–5** | `TODO` |
| **Why the restructuring eliminates it** | `TODO` |

### Point 3 — `TODO: title`

| | |
|---|---|
| **TMA friction** | `TODO` |
| **Artifact from Q2–5** | `TODO` |
| **Why the restructuring eliminates it** | `TODO` |

---

## Evidence index

All run logs and screenshots live under `evidence/`.

| File | Question | Status |
|---|---|---|
| `q2b-apply.log` | 2b | ☐ |
| `q2b-output.log` | 2b | ☐ |
| `q2b-s3-site.png` | 2b | ☐ |
| `q3a-bootstrap.log` | 3a | ☐ |
| `q3a-verify.log` | 3a | ☐ |
| `q3b-build-push.log` | 3b | ☐ |
| `q3b-ecr-images.log` | 3b | ☐ |
| `q3b-deploy.log` | 3b | ☐ |
| `q3b-verify.log` | 3b | ☐ |
| `q3c-idempotency.log` | 3c | ☐ |
| `q4a-frontend.log` | 4a | ☐ |
| `q4a-backend.log` | 4a | ☐ |
| `q4b-local-dev-network.png` | 4b | ☐ |
| `q4c-github-tags.png` | 4c | ☐ |
| `q4c-live-site-login.png` | 4c | ☐ |
| `q4c-webhook.png` | 4c | ☐ |
| `q4c-job-config.png` | 4c | ☐ |
| `q4c-credentials.png` | 4c | ☐ |
| `q4c-gate-red.png` | 4c | ☐ |
| `q4c-gate-green.png` | 4c | ☐ |
| `q4c-gate-merge.png` | 4c | ☐ |
| `q4c-gate-deploy.png` | 4c | ☐ |

## Submission checklist

- [ ] Every `TODO` above replaced
- [ ] Every evidence file committed and linked
- [ ] All written answers also pasted into the Canvas report
- [ ] Canvas report includes name, student ID and repository URL
- [ ] Final commit timestamp is before **Sunday 8 November 2026, 12:00 noon**
- [ ] No credentials committed (`.aws/`, `*.pem`, `.env`)