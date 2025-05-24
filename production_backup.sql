--
-- PostgreSQL database dump
--

-- Dumped from database version 16.8 (Debian 16.8-1.pgdg120+1)
-- Dumped by pg_dump version 17.5

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: daily_expenses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.daily_expenses (
    id integer NOT NULL,
    user_id integer,
    category_id integer,
    amount double precision NOT NULL,
    comment character varying,
    created_at timestamp without time zone
);


ALTER TABLE public.daily_expenses OWNER TO postgres;

--
-- Name: daily_expenses_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.daily_expenses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.daily_expenses_id_seq OWNER TO postgres;

--
-- Name: daily_expenses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.daily_expenses_id_seq OWNED BY public.daily_expenses.id;


--
-- Name: expense_categories; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.expense_categories (
    id integer NOT NULL,
    user_id integer,
    name character varying NOT NULL
);


ALTER TABLE public.expense_categories OWNER TO postgres;

--
-- Name: expense_categories_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.expense_categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.expense_categories_id_seq OWNER TO postgres;

--
-- Name: expense_categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.expense_categories_id_seq OWNED BY public.expense_categories.id;


--
-- Name: fixed_expenses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fixed_expenses (
    id integer NOT NULL,
    user_id integer,
    name character varying NOT NULL,
    amount double precision NOT NULL
);


ALTER TABLE public.fixed_expenses OWNER TO postgres;

--
-- Name: fixed_expenses_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fixed_expenses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fixed_expenses_id_seq OWNER TO postgres;

--
-- Name: fixed_expenses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fixed_expenses_id_seq OWNED BY public.fixed_expenses.id;


--
-- Name: forecast_scenarios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.forecast_scenarios (
    id integer NOT NULL,
    user_id integer,
    name text NOT NULL,
    months integer NOT NULL,
    income_changes double precision DEFAULT 0,
    fixed_changes double precision DEFAULT 0,
    extra_expenses json DEFAULT '[]'::json,
    projected_savings double precision,
    daily_budget double precision,
    total_free double precision,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.forecast_scenarios OWNER TO postgres;

--
-- Name: forecast_scenarios_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.forecast_scenarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.forecast_scenarios_id_seq OWNER TO postgres;

--
-- Name: forecast_scenarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.forecast_scenarios_id_seq OWNED BY public.forecast_scenarios.id;


--
-- Name: monthly_budget_adjustments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.monthly_budget_adjustments (
    id integer NOT NULL,
    user_id integer NOT NULL,
    month timestamp without time zone NOT NULL,
    source character varying NOT NULL,
    type character varying NOT NULL,
    amount double precision NOT NULL,
    comment character varying,
    apply_permanently integer,
    processed integer,
    created_at timestamp without time zone
);


ALTER TABLE public.monthly_budget_adjustments OWNER TO postgres;

--
-- Name: monthly_budget_adjustments_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.monthly_budget_adjustments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.monthly_budget_adjustments_id_seq OWNER TO postgres;

--
-- Name: monthly_budget_adjustments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.monthly_budget_adjustments_id_seq OWNED BY public.monthly_budget_adjustments.id;


--
-- Name: monthly_budgets; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.monthly_budgets (
    id integer NOT NULL,
    user_id integer,
    month_start date NOT NULL,
    income double precision NOT NULL,
    fixed double precision NOT NULL,
    savings_goal double precision NOT NULL,
    remaining double precision NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    coefficient double precision DEFAULT 1.0
);


ALTER TABLE public.monthly_budgets OWNER TO postgres;

--
-- Name: monthly_budgets_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.monthly_budgets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.monthly_budgets_id_seq OWNER TO postgres;

--
-- Name: monthly_budgets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.monthly_budgets_id_seq OWNED BY public.monthly_budgets.id;


--
-- Name: savings_balance; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.savings_balance (
    id integer NOT NULL,
    user_id integer,
    amount double precision DEFAULT 0.0
);


ALTER TABLE public.savings_balance OWNER TO postgres;

--
-- Name: savings_balance_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.savings_balance_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.savings_balance_id_seq OWNER TO postgres;

--
-- Name: savings_balance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.savings_balance_id_seq OWNED BY public.savings_balance.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    telegram_id bigint NOT NULL,
    name character varying,
    monthly_income double precision,
    monthly_savings double precision,
    created_at date DEFAULT '2025-05-17'::date,
    is_premium boolean DEFAULT false NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: daily_expenses id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_expenses ALTER COLUMN id SET DEFAULT nextval('public.daily_expenses_id_seq'::regclass);


--
-- Name: expense_categories id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_categories ALTER COLUMN id SET DEFAULT nextval('public.expense_categories_id_seq'::regclass);


--
-- Name: fixed_expenses id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fixed_expenses ALTER COLUMN id SET DEFAULT nextval('public.fixed_expenses_id_seq'::regclass);


--
-- Name: forecast_scenarios id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.forecast_scenarios ALTER COLUMN id SET DEFAULT nextval('public.forecast_scenarios_id_seq'::regclass);


--
-- Name: monthly_budget_adjustments id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.monthly_budget_adjustments ALTER COLUMN id SET DEFAULT nextval('public.monthly_budget_adjustments_id_seq'::regclass);


--
-- Name: monthly_budgets id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.monthly_budgets ALTER COLUMN id SET DEFAULT nextval('public.monthly_budgets_id_seq'::regclass);


--
-- Name: savings_balance id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.savings_balance ALTER COLUMN id SET DEFAULT nextval('public.savings_balance_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: daily_expenses; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.daily_expenses (id, user_id, category_id, amount, comment, created_at) FROM stdin;
2	1	34	23.33	MC Donalds	2025-05-17 08:36:03.51611
3	1	34	1.99	Circle K	2025-05-17 13:56:15.025213
4	1	32	48.28	Rimi	2025-05-17 14:51:57.54365
5	1	43	23.43	Meness Aptieka	2025-05-17 14:54:31.473527
6	1	44	6.2	My Fitness	2025-05-19 09:46:37.650883
7	1	33	9	Bistro Balts	2025-05-19 09:47:07.569053
8	1	42	400	Brio	2025-05-19 12:24:06.119601
9	1	32	9.71	Lidl	2025-05-19 16:23:17.516532
10	1	34	7.3	Rocket Bean	2025-05-20 05:49:11.279502
11	1	33	6.96	Lido	2025-05-20 10:57:02.112194
12	1	42	79	Premium	2025-05-20 13:08:09.809735
13	1	34	1.95	Narvessen	2025-05-20 13:26:12.940588
14	1	56	40	Higs	2025-05-20 14:33:45.097342
15	1	44	6.2	My Fitness	2025-05-21 08:18:20.532117
16	1	33	10	The Catch	2025-05-21 10:23:41.728772
17	1	47	336	Gural	2025-05-21 18:19:34.221167
18	1	34	2.29	Circle K	2025-05-22 07:28:44.344472
19	1	34	2.99	Narvessen	2025-05-22 07:29:37.483015
20	1	44	10	TM Gym	2025-05-22 07:33:20.667929
21	1	33	7.2	Lido	2025-05-22 10:07:59.866655
22	1	32	1.04	Rimi	2025-05-22 10:23:42.083054
23	1	50	28	Baloons	2025-05-22 15:52:03.264972
24	1	44	6.2	My Fitness	2025-05-23 08:32:39.991605
25	1	47	320	Turkey 2	2025-05-23 09:08:57.932568
26	1	34	3.5	Narvessen	2025-05-23 13:44:48.558566
27	1	34	21.98	Domino’s Pizza	2025-05-23 13:46:47.539211
28	1	37	48	Auto Port	2025-05-23 14:15:27.618277
29	1	32	9.98	Venden	2025-05-23 17:31:41.442683
30	1	32	38.11	Rimi	2025-05-23 17:34:26.127147
31	1	32	16.56	Rimi (Plov)	2025-05-23 17:35:36.330254
32	1	32	24.98	Super Alko	2025-05-23 18:31:53.810007
\.


--
-- Data for Name: expense_categories; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.expense_categories (id, user_id, name) FROM stdin;
29	1	Rent / Mortgage
30	1	Utilities
31	1	Home maintenance
32	1	Groceries
33	1	Restaurants
34	1	Coffee / Snacks
35	1	Fuel
36	1	Public Transport
37	1	Car Maintenance
38	1	Parking / Taxi
39	1	Clothing
40	1	Household Goods
41	1	Electronics
42	1	Medical
43	1	Pharmacy
44	1	Gym / Fitness
45	1	Cinema / Theater
46	1	Subscriptions / Streaming
47	1	Travel
48	1	Education
49	1	Kids supplies
50	1	Gifts & Holidays
51	1	Loans / Debts
52	1	Insurance
53	1	Taxes
54	1	Charity
55	1	Pets
56	1	Miscellaneous
\.


--
-- Data for Name: fixed_expenses; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.fixed_expenses (id, user_id, name, amount) FROM stdin;
4	1	Preschool	200
5	1	LMT	100
6	1	Mama	400
7	1	My Fitness	52
3	1	Annija	1500
\.


--
-- Data for Name: forecast_scenarios; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.forecast_scenarios (id, user_id, name, months, income_changes, fixed_changes, extra_expenses, projected_savings, daily_budget, total_free, created_at) FROM stdin;
\.


--
-- Data for Name: monthly_budget_adjustments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.monthly_budget_adjustments (id, user_id, month, source, type, amount, comment, apply_permanently, processed, created_at) FROM stdin;
\.


--
-- Data for Name: monthly_budgets; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.monthly_budgets (id, user_id, month_start, income, fixed, savings_goal, remaining, created_at, coefficient) FROM stdin;
4	1	2025-05-01	6500	2252	2000	1087.741935483871	2025-05-19 18:05:59.817643	0.4838709677419355
\.


--
-- Data for Name: savings_balance; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.savings_balance (id, user_id, amount) FROM stdin;
1	1	4220.365483870967
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, telegram_id, name, monthly_income, monthly_savings, created_at, is_premium) FROM stdin;
1	491964834	Vlad	6500	2000	2025-05-17	f
\.


--
-- Name: daily_expenses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.daily_expenses_id_seq', 32, true);


--
-- Name: expense_categories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.expense_categories_id_seq', 56, true);


--
-- Name: fixed_expenses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.fixed_expenses_id_seq', 8, true);


--
-- Name: forecast_scenarios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.forecast_scenarios_id_seq', 1, false);


--
-- Name: monthly_budget_adjustments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.monthly_budget_adjustments_id_seq', 6, true);


--
-- Name: monthly_budgets_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.monthly_budgets_id_seq', 4, true);


--
-- Name: savings_balance_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.savings_balance_id_seq', 1, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


--
-- Name: daily_expenses daily_expenses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_expenses
    ADD CONSTRAINT daily_expenses_pkey PRIMARY KEY (id);


--
-- Name: expense_categories expense_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_categories
    ADD CONSTRAINT expense_categories_pkey PRIMARY KEY (id);


--
-- Name: fixed_expenses fixed_expenses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fixed_expenses
    ADD CONSTRAINT fixed_expenses_pkey PRIMARY KEY (id);


--
-- Name: forecast_scenarios forecast_scenarios_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.forecast_scenarios
    ADD CONSTRAINT forecast_scenarios_pkey PRIMARY KEY (id);


--
-- Name: monthly_budget_adjustments monthly_budget_adjustments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.monthly_budget_adjustments
    ADD CONSTRAINT monthly_budget_adjustments_pkey PRIMARY KEY (id);


--
-- Name: monthly_budgets monthly_budgets_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.monthly_budgets
    ADD CONSTRAINT monthly_budgets_pkey PRIMARY KEY (id);


--
-- Name: savings_balance savings_balance_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.savings_balance
    ADD CONSTRAINT savings_balance_pkey PRIMARY KEY (id);


--
-- Name: savings_balance savings_balance_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.savings_balance
    ADD CONSTRAINT savings_balance_user_id_key UNIQUE (user_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_telegram_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_telegram_id_key UNIQUE (telegram_id);


--
-- Name: daily_expenses daily_expenses_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_expenses
    ADD CONSTRAINT daily_expenses_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.expense_categories(id);


--
-- Name: daily_expenses daily_expenses_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.daily_expenses
    ADD CONSTRAINT daily_expenses_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: expense_categories expense_categories_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_categories
    ADD CONSTRAINT expense_categories_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: fixed_expenses fixed_expenses_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fixed_expenses
    ADD CONSTRAINT fixed_expenses_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: forecast_scenarios forecast_scenarios_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.forecast_scenarios
    ADD CONSTRAINT forecast_scenarios_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: monthly_budget_adjustments monthly_budget_adjustments_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.monthly_budget_adjustments
    ADD CONSTRAINT monthly_budget_adjustments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: monthly_budgets monthly_budgets_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.monthly_budgets
    ADD CONSTRAINT monthly_budgets_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: savings_balance savings_balance_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.savings_balance
    ADD CONSTRAINT savings_balance_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

