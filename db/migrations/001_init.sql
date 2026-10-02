-- Schemat startowy systemu dla klubów.
-- Kwoty są zawsze w groszach (int), czasy w timestamptz (UTC), strefa klubu to Europe/Warsaw.

create table orgs (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique check (slug ~ '^[a-z0-9][a-z0-9-]{1,39}$'),
  name text not null,
  kind text not null default 'club' check (kind in ('club', 'organizer')),
  city text,
  address text,
  capacity int check (capacity is null or capacity > 0),
  plan text not null default 'start' check (plan in ('start', 'klub', 'premium')),
  -- kto płaci opłatę serwisową: kupujący (doliczana do ceny) albo klub (potrącana z faktury)
  fee_payer text not null default 'buyer' check (fee_payer in ('buyer', 'org')),
  -- 'none' = bez płatności online (noc testowa), 'mock' = symulator, 'przelewy24' = konto klubu w P24
  payment_provider text not null default 'none' check (payment_provider in ('none', 'mock', 'przelewy24')),
  p24_merchant_id int,
  p24_pos_id int,
  p24_crc_enc text,
  p24_api_key_enc text,
  p24_sandbox boolean not null default true,
  contact_email text,
  instagram text,
  created_at timestamptz not null default now()
);

create table users (
  id uuid primary key default gen_random_uuid(),
  email text not null,
  name text not null,
  password_hash text not null,
  created_at timestamptz not null default now()
);
create unique index users_email_key on users (lower(email));

create table sessions (
  token_hash text primary key,
  user_id uuid not null references users (id) on delete cascade,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null
);
create index sessions_user_idx on sessions (user_id);

create table login_attempts (
  id bigserial primary key,
  email text not null,
  ok boolean not null,
  at timestamptz not null default now()
);
create index login_attempts_email_idx on login_attempts (lower(email), at);

create table memberships (
  org_id uuid not null references orgs (id) on delete cascade,
  user_id uuid not null references users (id) on delete cascade,
  role text not null check (role in ('owner', 'manager', 'door')),
  created_at timestamptz not null default now(),
  primary key (org_id, user_id)
);
create index memberships_user_idx on memberships (user_id);

create table promoters (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references orgs (id) on delete cascade,
  name text not null,
  code text not null check (code ~ '^[A-Z0-9]{3,16}$'),
  phone text,
  email text,
  panel_token_hash text unique,
  ticket_commission_pct numeric(5, 2) not null default 0 check (ticket_commission_pct between 0 and 100),
  guest_commission int not null default 0 check (guest_commission >= 0), -- grosze za gościa, który wszedł
  active boolean not null default true,
  created_at timestamptz not null default now(),
  unique (org_id, code)
);

create table events (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references orgs (id) on delete cascade,
  slug text not null check (slug ~ '^[a-z0-9][a-z0-9-]{1,79}$'),
  name text not null,
  description text not null default '',
  venue_name text,
  starts_at timestamptz not null,
  ends_at timestamptz not null,
  capacity int check (capacity is null or capacity > 0),
  min_age int check (min_age in (16, 18, 21)),
  status text not null default 'draft' check (status in ('draft', 'published', 'cancelled')),
  created_at timestamptz not null default now(),
  unique (org_id, slug),
  check (ends_at > starts_at)
);
create index events_org_idx on events (org_id, starts_at);

-- Pule cenowe: w obrębie tier_group w sprzedaży jest pierwsza (wg sort_order) pula,
-- która ma wolne bilety i mieści się w oknie sprzedaży. Wyprzedanie puli = automatyczny skok ceny.
create table ticket_types (
  id uuid primary key default gen_random_uuid(),
  event_id uuid not null references events (id) on delete cascade,
  tier_group text not null default 'Wejście',
  name text not null,
  price int not null check (price >= 0),
  quantity int not null check (quantity >= 0),
  group_size int not null default 1 check (group_size between 1 and 20),
  sales_start timestamptz,
  sales_end timestamptz,
  sort_order int not null default 0,
  active boolean not null default true,
  created_at timestamptz not null default now()
);
create index ticket_types_event_idx on ticket_types (event_id);

create table discount_codes (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references orgs (id) on delete cascade,
  event_id uuid references events (id) on delete cascade,
  code text not null check (code ~ '^[A-Z0-9-]{3,24}$'),
  percent_off int not null check (percent_off between 1 and 100),
  max_uses int check (max_uses is null or max_uses > 0),
  used int not null default 0,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  unique (org_id, code)
);

create table lounges (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references orgs (id) on delete cascade,
  name text not null,
  zone text not null default 'Sala główna',
  capacity int not null check (capacity > 0),
  max_capacity int not null,
  base_price int not null check (base_price >= 0),
  extra_person_price int not null default 0 check (extra_person_price >= 0),
  min_spend int not null default 0 check (min_spend >= 0),
  prepay_percent int not null default 50 check (prepay_percent between 0 and 100),
  -- położenie na mapie sali, w procentach szerokości/wysokości planu
  map_x numeric(5, 2) not null default 10,
  map_y numeric(5, 2) not null default 10,
  map_w numeric(5, 2) not null default 14,
  map_h numeric(5, 2) not null default 12,
  sort_order int not null default 0,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  check (max_capacity >= capacity)
);
create index lounges_org_idx on lounges (org_id);

create table orders (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references orgs (id),
  event_id uuid not null references events (id),
  public_token text not null unique,
  kind text not null check (kind in ('tickets', 'lounge')),
  status text not null default 'pending' check (status in ('pending', 'paid', 'cancelled', 'refunded')),
  buyer_name text not null,
  buyer_email text not null,
  buyer_phone text,
  lang text not null default 'pl' check (lang in ('pl', 'en')),
  subtotal int not null check (subtotal >= 0),
  service_fee int not null check (service_fee >= 0),
  total int not null check (total >= 0),
  fee_payer text not null check (fee_payer in ('buyer', 'org')),
  promoter_id uuid references promoters (id) on delete set null,
  discount_code_id uuid references discount_codes (id) on delete set null,
  marketing_consent boolean not null default false,
  payment_provider text not null,
  provider_order_id text,
  expires_at timestamptz not null,
  paid_at timestamptz,
  created_at timestamptz not null default now()
);
create index orders_event_idx on orders (event_id, status);
create index orders_promoter_idx on orders (promoter_id) where promoter_id is not null;

create table lounge_reservations (
  id uuid primary key default gen_random_uuid(),
  event_id uuid not null references events (id) on delete cascade,
  lounge_id uuid not null references lounges (id),
  status text not null check (status in ('requested', 'pending_payment', 'confirmed', 'paid', 'cancelled', 'no_show')),
  name text not null,
  phone text,
  email text,
  persons int not null check (persons > 0),
  total_price int not null check (total_price >= 0),
  prepay_amount int not null check (prepay_amount >= 0),
  order_id uuid references orders (id),
  promoter_id uuid references promoters (id) on delete set null,
  source text not null default 'web' check (source in ('web', 'phone', 'dm', 'panel')),
  notes text,
  code text not null unique,
  hold_until timestamptz,
  checked_in_at timestamptz,
  created_at timestamptz not null default now()
);
create index lounge_res_event_idx on lounge_reservations (event_id, lounge_id);
-- Zabezpieczenie przed podwójną rezerwacją tej samej loży na tę samą noc.
create unique index lounge_res_one_active on lounge_reservations (event_id, lounge_id)
  where status in ('confirmed', 'paid');

create table order_items (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references orders (id) on delete cascade,
  ticket_type_id uuid references ticket_types (id),
  lounge_reservation_id uuid references lounge_reservations (id),
  quantity int not null check (quantity > 0),
  unit_price int not null check (unit_price >= 0),
  unit_fee int not null check (unit_fee >= 0),
  check ((ticket_type_id is null) <> (lounge_reservation_id is null))
);
create index order_items_order_idx on order_items (order_id);
create index order_items_tt_idx on order_items (ticket_type_id);

create table tickets (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references orders (id),
  event_id uuid not null references events (id) on delete cascade,
  ticket_type_id uuid not null references ticket_types (id),
  code text not null unique,
  status text not null default 'valid' check (status in ('valid', 'void')),
  checked_in_at timestamptz,
  created_at timestamptz not null default now()
);
create index tickets_event_idx on tickets (event_id);
create index tickets_order_idx on tickets (order_id);

create table guest_lists (
  id uuid primary key default gen_random_uuid(),
  event_id uuid not null references events (id) on delete cascade,
  name text not null,
  promoter_id uuid references promoters (id) on delete set null,
  capacity int not null check (capacity > 0),
  entry_until timestamptz,
  created_at timestamptz not null default now()
);
create index guest_lists_event_idx on guest_lists (event_id);

create table guest_entries (
  id uuid primary key default gen_random_uuid(),
  list_id uuid not null references guest_lists (id) on delete cascade,
  event_id uuid not null references events (id) on delete cascade,
  full_name text not null,
  name_key text not null,
  phone text,
  email text,
  plus_ones int not null default 0 check (plus_ones between 0 and 20),
  code text not null unique,
  status text not null default 'invited' check (status in ('invited', 'void')),
  checked_in_at timestamptz,
  created_by text,
  created_at timestamptz not null default now()
);
create index guest_entries_event_idx on guest_entries (event_id, name_key);
create index guest_entries_list_idx on guest_entries (list_id);

-- Bilety sprzedane na innych platformach (RA, Going, Biletomat...) wczytane do jednej bramki.
create table external_tickets (
  id uuid primary key default gen_random_uuid(),
  event_id uuid not null references events (id) on delete cascade,
  source text not null check (source in ('ra', 'going', 'biletomat', 'ebilet', 'other')),
  code text not null,
  holder_name text,
  ticket_label text,
  checked_in_at timestamptz,
  created_at timestamptz not null default now(),
  unique (event_id, code)
);

-- Baza gości klubu (CRM). Dane przetwarzane w imieniu klubu (umowa powierzenia).
create table guests (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references orgs (id) on delete cascade,
  email text,
  phone text,
  name text,
  marketing_consent boolean not null default false,
  consent_at timestamptz,
  consent_source text,
  orders_count int not null default 0,
  total_spent int not null default 0,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  anonymized_at timestamptz
);
create unique index guests_org_email_key on guests (org_id, lower(email)) where email is not null;

-- Dostęp telefonów bramki bez zakładania kont (link z tokenem, ważny do końca nocy).
create table door_tokens (
  id uuid primary key default gen_random_uuid(),
  event_id uuid not null references events (id) on delete cascade,
  label text not null,
  token_hash text not null unique,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null,
  revoked_at timestamptz
);

-- Dziennik bramki: skany, wejścia i wyjścia z licznika. client_id czyni synchronizację idempotentną.
create table door_events (
  id bigserial primary key,
  event_id uuid not null references events (id) on delete cascade,
  device_id text not null,
  client_id text not null,
  type text not null check (type in ('scan', 'in', 'out')),
  code text,
  ref_kind text check (ref_kind in ('ticket', 'guest', 'lounge', 'external')),
  ref_id uuid,
  persons int not null default 1 check (persons between 0 and 50),
  result text not null check (result in ('ok', 'override', 'duplicate', 'invalid', 'void', 'too_late', 'counter')),
  label text,
  occurred_at timestamptz not null,
  received_at timestamptz not null default now(),
  unique (event_id, client_id)
);
create index door_events_event_idx on door_events (event_id, id);
