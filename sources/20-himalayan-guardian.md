# Himalayan Guardian CTG 逐条款核查

抓取日期 2026-08-27。核查对象是 Himalayan Guardian Nepal Pvt. Ltd.（HGN）在 `https://www.himalayanguardian.com/` 出售的 Comprehensive Tourism Guard（CTG），承保方尼泊尔 IGI Prudential Insurance Limited，保单条款名《Nepal Travel Personal Accident Insurance (2025 Edition)》。核查口径同 `sources/19`：6 名中国大陆居民、14 天、徒步最高点 Kala Patthar 5,545m。

站点是 React 单页应用，条款正文不在 HTML 里。四份 CTG 官方文件由站点自己的公开接口给出：`https://api.himalayanguardian.com/api/public/docs/templates?groupCode=CHECKOUT_CTG&active=true` 返回 5 条记录，各带一个 24 小时有效的 S3 直链，分别是 Insurance Clause (CTG)、Important Notes For Policy Holders (CTG)、CTG Contract、Health Self Declaration (CTG)、Device Instructions。本文所有条款引用都取自这批 PDF 原文。同接口的 `groupCode=CHECKOUT_KAK` 返回另一套文件，那是 Kailash Rakshya Kavach（KAK），投保须知第 1 条写「This insurance product covers accidental injuries occurring during Kailash or Manasarovar Kora within the territory of China」，承保区域在中国境内，与 EBC 无关。

## 要点

- CTG 在保险责任条文里点名承保高原反应：意外医疗责任写「accidental bodily injury **or acute mountain sickness**」，紧急医疗运送责任写「an accidental injury ... or experience **altitude sickness**」，这是三家产品里唯一把高反写进保险责任正文的。
- 代价是高反有一套硬性认定门槛：血氧须低于按海拔分档的阈值（≥5,500m 时低于 70%），或经医生诊断肺水肿、脑水肿；申请时要交三段各 ≥30 秒的血氧仪录像，三段读数都要达标。
- 按 EBC 线路自动匹配到的是 ≤5,500m 档（14 天 USD 109），但 Kala Patthar 越过 5,500m，官网自己的 EBC 页面提示要买 ≤6,000m 档（14 天 USD 169）；投保须知写明事故地点超过所购计划的海拔上限不予赔付。
- 紧急医疗运送额度只有 USD 4,500（≤5,500m 档）或 USD 6,000（≤6,000m 档），对照 Gorak Shep 撤离到加德满都 USD 4,000–8,000 的实际报价刚够到下沿；高反导致的运送还要自付 15%。
- 救援方式由 Call Center 决定而不是被保险人，合同把「人力背运」与直升机并列写进备选方案，并写明未经其安排的救援费用不承担。
- HGN 2025-07 才在加德满都成立，2025-08 拿到 NTA 与 NIA 批准，2025-09-26 第一单客户，官网自报「100+ Trekkers Protected」；执行救援的合作方 Alpine Rescue Service Pvt. Ltd. 是 2012 年起营业的老公司，自报 5,000+ 架次救援飞行。

## 一、产品结构与承保方

CTG 合同《Comprehensive Tourism Guard (CTG) Service Sales Contract》BASIC DEFINITIONS 部分把三方写清楚：

> VI　Insurer: Refers to a legitimate insurance company that has a clear written contractual proof with HGN (as of the signing date of this Contract) to provide insurance services. For the purpose of this Contract, it refers to IGI Prudential Insurance Company Limited (hereinafter referred to as IGIP), with PAN/VAT No. 69855056 and registered address at 5th Floor, BHIM PLAZA, NAXAL, KATHMANDU, NEPAL.

> VII　We ...：⚫ The signing entity, devices and platform service provider: Himalayan Guardian Nepal Pvt. Ltd. (hereinafter referred to as HGN), with PAN/VAT No.622379586 and registered address at Dhumbarahi,04 Kathmandu Nepal; ⚫ The Insurer; ⚫ The provider of emergency medical evacuation and accidental medical services: a legitimate institution that has a clear written contractual proof with the signing entity of this Contract (or the Insurer) (as of the signing date of this Contract) to provide relevant services.

合同正文不点名救援执行方，只写「a legitimate institution」。名字出现在官网：`https://www.himalayanguardian.com/rescue-process` 与 `/our-partners` 写「Our Official Partner: Alpine Rescue Service Pvt. Ltd.」「The designated in-country operational arm for insurers and global assistance companies across Nepal.」，CTG FAQ 直接问答「Who is CTG's rescue partner? — Alpine Rescue Service.」

FAQ 另写明理赔决定权在承保方而不是 HGN：

> Who approves CTG insurance claims? — IGI Prudential Insurance Limited. HGN assists with documentation but does not decide claims.

## 二、四个海拔档位的保额与保费

站点自带的价目数据文件 `https://www.himalayanguardian.com/assets/pricingData-D6nGdwYt.js` 给出四档保额（美元）：

| 档位（事故地点海拔上限） | 意外身故及伤残 | 意外／高反医疗 | 紧急医疗运送 | 遗体运返 |
|---|---|---|---|---|
| ≤2,000m | 35,000 | 2,000（仅意外） | 2,000 | 2,000 |
| ≤3,500m | 35,000 | 2,000（仅意外） | 3,000 | 2,000 |
| ≤5,500m | 35,000 | 3,500（意外与高反） | 4,500 | 2,000 |
| ≤6,000m | 17,500 | 3,500（意外与高反） | 6,000 | 2,000 |

前两档的项目名是 "Accidental Medical"，后两档是 "Accidental & AMS Medical Treatment"，高反医疗只在 ≤5,500m 与 ≤6,000m 两档里。升到 ≤6,000m 档时意外身故及伤残从 35,000 降到 17,500，紧急医疗运送从 4,500 升到 6,000。

18–60 岁、14 天、不带设备的保费：≤2,000m USD 13、≤3,500m USD 18、≤5,500m USD 109、≤6,000m USD 169。同一格带设备分别是 13 / 18 / 162 / 221。

用站点自己的报价接口复核（2026-08-27 实测）：

```
POST https://api.himalayanguardian.com/api/quotes/generate
{"nationality":"China","ages":[32],"duration":14,"startDate":"2026-09-25","maxAltitude":5364}
→ CTG/5500M/14D/60Y  USD 109  LIB_DEATH=35000 LIB_AMS=3500 LIB_TRANSPORT=4500 LIB_REPATRIATE=2000

同样参数 maxAltitude 改成 5545
→ CTG/6000M/14D/60Y  USD 169  LIB_DEATH=17500 LIB_AMS=3500 LIB_TRANSPORT=6000 LIB_REPATRIATE=2000
```

接口接受 `nationality: China`，报价流程没有国籍或居住地校验。

### EBC 线路自动匹配到 ≤5,500m 档，Kala Patthar 越线

公开线路库 `https://api.himalayanguardian.com/api/public/routes` 里 EBC 那一条：

```json
{"name":"Everest Base Camp","abbreviation":"EBC","maxAltitude":5364,"durationDays":14,"difficultyLevel":"HARD","isHighAltitude":true}
```

登记的最高海拔是 5,364m，即 EBC 本体，不含 Kala Patthar。在报价页选 EBC 线路，海拔自动填 5,364m，匹配到 ≤5,500m 档。

投保须知第 1 条第 1 款把越线的后果写死：

> For Standard Routes, policyholders may select a corresponding coverage plan based on the specific altitude of the route. **The Insurer shall not be liable for any compensation if the location of the accident exceeds the maximum altitude stipulated in the insured plan.**

官网的 EBC 专页 `https://www.himalayanguardian.com/everest-base-camp-insurance` 自己给出提示，原文：

> Before you select a plan — Base Camp itself falls in CTG's ≤5,500m tier — but Kala Patthar, at roughly 5,644m, crosses into the ≤6,000m tier. If an accident occurs above the ceiling of your purchased plan, it may fall outside your insurance liability, so confirm your itinerary's actual highest point, including any side trips, before choosing.

该页把 Kala Patthar 写作 5,644m，与本报告采用的 5,545m 不同，两个数字都在 5,500m 线以上，结论一致：登 Kala Patthar 要买 ≤6,000m 档。

## 三、高原反应写在保险责任里，但有硬性认定门槛

《INSURANCE CLAUSES》ARTICLE 5 第 3 款（意外医疗责任）原文：

> During the insurance period, if the insured, while traveling within the territory of Nepal with valid documents, suffers an accidental bodily injury **or acute mountain sickness meeting specified physical conditions (as defined herein)**, and receives reasonable and necessary medical treatment at a medical institution within Nepal, the insurer shall settle the claim after deducting the deductible amount agreed in the contract. The period of medical treatment shall be counted from the date of the incident and shall not exceed 90 days in total.

同条第 4 款（紧急医疗运送责任）原文：

> During the insurance period, if the insured holds valid documents and is traveling in Nepal, they may suffer from an accidental injury as specified in the insurance contract **or experience altitude sickness (as defined)**. If the rescue agency entrusted by the insurer or its authorized representative (hereinafter referred to as "the rescue agency") deems it necessary for medical reasons, the insured will be transported to a hospital in the local area or another nearby region that meets the treatment requirements.

PARAPHRASE 第 3 条给出高反的认定标准：

> ALTITUDE SICKNESS — Clinically referred to as acute mountain sickness (AMS) ... Altitude sickness covered under the insurance policy is defined as the occurrence of any one of the following conditions:
> 1) The insured's Oxygen saturation (SpO2) must meet below requirements:

| Altitude | SpO2 |
|---|---|
| Less than 3500 meters | Less than 85% |
| 3500 meters ≤ Altitude ＜ 4500 meters | Less than 80% |
| 4500 meters ≤ Altitude ＜ 5500 meters | Less than 75% |
| Altitude ≥ 5500 meters | Less than 70% |

> 2) Expectoration of pink frothy sputum, or pulmonary edema diagnosed by a qualified medical practitioner.
> 3) Cerebral edema as diagnosed by a doctor;

### 举证要求：三段血氧录像

投保须知第 10 条：

> When the Insured applies for emergency rescue due to altitude sickness, blood oxygen test videos must be submitted. The Insured or accompanying guide shall record a video of no less than 30 seconds showing the readings (heart rate and blood oxygen) from the Insured's fingertip pulse oximeter. The video must capture the entire testing process and the overall physical condition of the Insured. 3(Three) such videos are required, **with an interval of no less than 15 minutes** between each recording. The blood oxygen readings in all three videos must meet the insured conditions for altitude sickness.

CTG 合同的对应脚注把间隔写成 5 分钟：

> VIDEO RECORDING REQUIREMENTS: The time interval between two consecutive videos shall be no less than 5 minutes, and the duration of each video shall be no less than 30 seconds. ... The entire video shall be continuous, complete and unedited.

两份文件对间隔时长口径不一致（15 分钟 vs 5 分钟），下单前要书面确认按哪个执行。理赔材料清单里也单列了这一项：ARTICLE 16 第 4 款「Application for emergency medical transport insurance ... 2) The insurer needs the test certificate of vital signs in altitude sickness」。

### 责任免除里的「illness」没有为高反开口子

ARTICLE 6 责任免除第 4 项原文：

> 4. The insured's pregnancy, abortion, delivery, **illness** and drug allergy;

这一项适用于「death, disability, accidental medical treatment, emergency medical transport or repatriation of the body」全部五项责任，条文本身没有写「高原反应除外于本项」。保险责任正文点名承保高反、投保须知给出高反的认定标准与专属自付比例，说明产品意图是承保高反；但免除条款里这个不加限定的 illness 与之并存，是这份条款里第二处需要书面澄清的地方。

第 12 项另把「adventure activities」列为除外，PARAPHRASE 第 10 条给的定义是：

> ADVENTURE ACTIVITIES — refers to the act of deliberately putting oneself in a situation where there is a risk of losing one's life or injuring one's body under certain natural conditions. For example, river rafting, hiking through deserts or virgin forests rarely visited by human beings.

举的例子是漂流与穿越荒漠原始林，EBC 商业徒步线不属于「rarely visited by human beings」，但这条定义写得宽。

## 四、免赔与自付比例

投保须知第 11 条：

> For accidental injury medical treatment, there is a deductible of USD 100 per incident. For emergency medical transportation liability caused by altitude sickness that meets the emergency medical transportation conditions, the insured shall bear a **15% co-payment ratio**; for emergency medical transportation liability caused by accidental reasons, there is no deductible or co-payment ratio.

按 ≤6,000m 档的 USD 6,000 上限算，一次 USD 6,000 的高反直升机撤离，保险赔 85% 即 USD 5,100，自付 USD 900；撤离报价到 USD 8,000 时保险赔满 6,000，自付 2,000。

## 五、救援方式由谁决定

投保须知第 9 条：

> If the rescue agency entrusted by the insurer or its authorized representative deems it necessary to carry out emergency medical transportation from a medical perspective, the insured will be transported to a hospital in the local area or other nearby areas that meets the treatment conditions. **The rescue agency has the right to decide the means of emergency medical transportation and the destination. After transportation to the nearest hospital, the emergency medical transportation liability will terminate.**

投保须知第 7 条：

> The Insured must seek rescue assistance either by triggering the SOS alarm button (if equipped with a device) or by calling the 24-hour emergency hotline designated by the Insurer ... **The Insurer shall not compensate any expenses incurred from rescue arrangements made independently by the Insured.**

CTG 合同 ARTICLE XLV 与脚注 14：

> The Emergency Medical Transportation included in this service only guarantees an optimal standardized transportation plan in emergency situations, not the most comfortable plan (or a personalized plan proactively requested by the Guarded).

> OPTIMAL STANDARDIZED TRANSPORT PLAN: Refers to the plan where we transport the Guarded to the nearest location where their vital signs can be restored to normal and stable, in a manner that best balances operational convenience, cost-effectiveness, feasibility, and timeliness ... **We do not promise to use helicopters, ambulances, or any other transport methods subjectively deemed necessary by the Guarded**; however, we promise that the method adopted will not cause harm to the health and life safety of the Guarded in an emergency.

EMERGENCY MEDICAL TRANSPORTATION PROCEDURES 第 10 步脚注 30 给出筛选顺序，与脚注 14 的排列不同：

> OPTIMAL: The Call Center will sequentially screen out the final plan based on the **priority order of timeliness, feasibility, operational convenience, and cost-effectiveness**. The final plan includes but is not limited to one or more of all possible means such as **helicopters, ambulances, general motor vehicles, animal-powered transport, and manual carrying**. It is important to note that if the final plan has to make a choice between the Guarded's life safety and other harms, the Call Center will give priority to ensuring the Guarded's life safety.

脚注 30 把时效放在第一位、成本放在最后，脚注 14 把成本放在时效前面，两处措辞不一致。备选方案里「manual carrying」（人力背运）与直升机并列。

流程第 9、12、14 步写清三个终止点：Call Center 判定不需要撤离而被保险人坚持要，改为自费报价；被保险人拒绝确认方案或费用，流程终止，另行自行安排的与本合同无关；救援公司到现场核实与描述不符，有权拒绝执行并要求被保险人赔偿已发生的费用。

官网 FAQ 用同样口径回答直升机问题：

> Does CTG include helicopter evacuation? — Yes, as one possible form of Emergency Medical Transportation, determined by medical need and on-ground conditions — not as an automatic or guaranteed outcome for every incident.

> How does SOS work? — SOS sends a distress alert via Tracer M3 or the Emergency Call Center, which starts location verification, situation assessment, and rescue coordination. **It doesn't automatically dispatch a specific transport method.**

## 六、保障范围只在尼泊尔境内

CTG 合同 USER NOTICE 第 1 条：

> APPLICABILITY: This service is applicable only in case when the Guarded physically present within the territory of Nepal and in possession of valid and lawful travel documentation. Coverage shall not extend to any guarded outside the territorial jurisdiction of Nepal or to any individual lacking proper entry permits, visas, or other legally required authorizations.
> Exception: Corpse Repatriation shall be done to their respective home country upon fulfilling all the procedures from their heir or beneficiary or related bodies.

保险条款 ARTICLE 5 第 1 款的身故责任要求「has not left Nepal until death」，第 3 款的医疗责任要求「receives ... medical treatment at a medical institution within Nepal」。ARTICLE 9 写保险责任起于「the date on which the insured enters Nepal or The date on which insured will begin his journey/trekking」中的较晚者，止于保险期届满或「the insured leaves the territory of Nepal」中的较早者。

净效果：没有回国医疗运送责任，只有遗体运返回国；撤到加德满都的医院之后就出保障范围了，之后回国治疗的费用不在这份保单里。

## 七、投保条件与行为义务

- 年龄：投保须知第 3 条「This insurance covers age ranges from 18 to 70 years old(inclusive)」。
- 承保对象：保险条款 ARTICLE 2「This contract covers all the Nationalities including Nepalese Trekkers but excludes Sherpas Guides and Porters. This Insurance should be taken before beginning of journey/trekking.」向导与背夫不在承保对象内。
- 投保时点：官网 FAQ「Can I buy CTG after arriving in Nepal? — Yes, provided your trek or journey hasn't started yet. You select your intended start date, and coverage begins from that date.」CTG 合同 ARTICLE X 写平台在出发日 T-2 日 00:00 自动出单，ARTICLE XI 允许要求立即出单。
- 必须带血氧仪：投保须知第 4 条「When engaging in high-altitude mountaineering at elevations above 2,500 meters, the Insured must carry a fingertip pulse oximeter.」
- 每日爬升速率：投保须知第 5 条要求 ≤3,500m 每日爬升 ≤1,000m，3,500–4,500m ≤700m，4,500–5,500m ≤600m，5,500–6,500m ≤500m，并写「If the Insured suffers from altitude sickness due to forced rapid ascent, the Insurer reserves the right to reject the claim according to the actual circumstances.」
- 出现症状先自救再下撤：投保须知第 6 条要求先在最近休息点休息、喝热水／吸氧／服药，「then must immediately descend with the assistance of a guide or companion」。
- 不得偏离合法旅游线路：投保须知第 2 条「If the insured has an insurance accident while deviating from the legally permitted tourist routes by the Nepalese government, the insurer shall not bear any liability for compensation.」
- 报案与材料时限：保险条款 ARTICLE 15「must promptly notify the insurer within 48 hours and submit the required claim documents to the insurer within 21 days」。
- 退款：投保须知第 12 条「Once this insurance is purchased, no refund will be made.」；CTG 合同 ARTICLE XIII 写出单前可撤单、扣 15% 后退还余额，ARTICLE XII 写出单后不可撤销、不可退款。

### 健康告知不实会让高反相关保障整体失效

《HEALTH SELF-DECLARATION》原文：

> I hereby solemnly declare that I have never suffered from, nor am I currently suffering from, any of the diseases or symptoms listed in the following NOTIFICATION TABLE OF EXCLUSIVE HEALTH CONDITIONS. If I fail to truthfully disclose any of the following health conditions or past medical history, **any insurance coverage relating to Acute Mountain Sickness (AMS), High Altitude Pulmonary Edema (HAPE), High Altitude Cerebral Edema (HACE), or any other conditions arising from or related to AMS shall automatically become void.** IGI Prudential Insurance Limited shall bear no liability for any such insurance claims or coverage, and all fees already collected shall be non-refundable.

告知表列出的条目里，对普通徒步者最容易踩到的是：高血压（收缩压 ≥160 mmHg 或舒张压 ≥100 mmHg）、糖尿病或空腹血糖 >6.2 mmol/L、哮喘、慢性支气管炎与肺气肿、贫血、肝炎病毒携带者、未愈合的四肢骨折或软组织损伤、怀孕。

官网 FAQ 说明带既往症也可能投保成功但高反保障被剔除：

> Can travellers with medical conditions buy CTG? — Declared conditions are referred to IGI Prudential for review. If approved, you may be accepted with AMS-related coverage excluded; the decision belongs to the insurer.

## 八、救援执行方与响应时效

官网 `https://www.himalayanguardian.com/rescue-process` 关于 Alpine Rescue Service Pvt. Ltd.：

> Alpine Rescue Service Pvt. Ltd. is a Trademark Registered company, duly registered with the Office of the Company Registrar and licensed by the Department of Tourism, Ministry of Culture, Tourism and Civil Aviation, Government of Nepal. ARS has been operating within Nepal's legal framework since 2012, backed by Professional Liability Insurance with coverage of USD 500,000.

同页给出 ARS 的自报数字：5,000+ Rescue Flights Completed、6,000+ Clients Served、14+ Years of Operations、50+ Global Insurance Partners，另称 2016 年在柏林获 International Assistance Group Quality Award、2015 年尼泊尔地震期间执行约 700 架次飞行。

响应时效的表述：

> HGN targets rescue dispatch within 30 minutes of alert activation. Actual helicopter dispatch depends on weather, aircraft availability, and distance from the nearest airstrip. Most Himalayan trekking areas are within 30–90 minutes of helicopter reach, weather permitting.

> Helicopter response times in Nepal depend on weather, daylight, and visibility at altitude: in good conditions a rescue can reach Everest Base Camp within 90 minutes of dispatch, but storms or low cloud may delay flights until a safe window opens.

写的是目标（targets）不是承诺。

24 小时救援电话（`https://www.himalayanguardian.com/emergency` 与 `/contact`）：+977-9801068400（主）、+977-9851232668（备用，同号 WhatsApp）、+977-1-4964222（座机）、operation@alpine-rescue.com。IGI Prudential 的理赔电话另列：01-5971516、免费线 1660-01-79353。

## 九、公司资历

官网 `https://www.himalayanguardian.com/our-story` 的时间线原文：

> July 12 — Company Establishment in Kathmandu — The enterprise was formally established in Kathmandu...
> August — Regulatory Approval — Nepal Telecommunications Authority (NTA) — HGN obtained official approval for device communication and connectivity compliance.
> August — Regulatory Approval — Nepal Insurance Authority (NIA) — HGN's strategic partner IGI Prudential obtained official approval for tailored insurance products. An exclusive sales agreement between HGN and IGI Prudential authorizes HGN to be the sole distributor of these tailored insurance products by integrating them into the CTG service.
> September 26 — First Order Execution — Successful onboarding of the first client(s), demonstrating market acceptance and operational readiness.

第一起救援案例，同页：

> A client suffering from severe Acute Mountain Sickness (AMS) was rescued from Dzongla in the Everest Region (4,826 m) and transferred to Lukla, then admitted to a hospital — all within a total of 33 minutes.

正文另写「In October 2025, that system met its first true test」，即该案例发生在 2025-10。HGN 自报的运营数字在 `/about-device` 页：「100+ Trekkers Protected」「6 Rescue Partners」「&lt;30min Avg Response Time」。站上没有 HGN 自身的累计赔付金额或赔案数。

NTA 与 NIA 的批准表述只有文字，遍历站点资源没有找到批准文号或证书编号。

## 十、投保与付款

- 购买渠道：CTG 合同 ARTICLE I「all services must be purchased through the platform」，个人可在 `https://www.himalayanguardian.com/quote` 自助下单，未找到必须经旅行社购买的表述。
- 支付方式（`https://www.himalayanguardian.com/supported-payments`）：Visa、Mastercard 走 3D Secure 网关，「international transactions supported」；二维码支付支持 Fonepay、**Alipay**、UPI、eSewa、Khalti。遍历站点资源没有出现 WeChat Pay。
- Tracer M3 设备：BDS+GPS 双模、专用 SOS 物理按键、续航 240 小时、IP67、工作温度 −30°C 至 +60°C，主动定位间隔 30 秒。`/about-device` 页写「Included Free with All Plans Above 5,500m」并收「Refundable $150 deposit」；但站点自己的价目数据文件里 withDevice 与 withoutDevice 两列在 ≤6,000m／14 天／18–60 岁这一格分别是 USD 221 与 USD 169，差 USD 52。两处口径不一致，下单前要问清。FAQ 写设备非强制：「Is Tracer M3 mandatory? — No. It's optional and typically associated with higher-altitude or full-package plans.」

## 对照本行程的三处待确认项

1. 三段血氧录像的间隔按 15 分钟还是 5 分钟——投保须知与合同脚注写法不同。凌晨登 Kala Patthar 途中出现 HAPE／HACE 时，按 15 分钟口径完成三段录像要 30 分钟以上。
2. 责任免除第 4 项那个不加限定的「illness」与保险责任正文点名承保高反之间的关系。
3. 第 6 天 Dingboche 适应日上到 Nangkartshang 山脊约 5,080m，自 4,410m 起算当日爬升约 670m。投保须知第 5 条对 4,500–5,500m 段的限值是每日 600m，按整日累计爬升算越限、按 4,500m 以上区段单算（约 580m）不越限，口径需要确认。
