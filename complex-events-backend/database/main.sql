/*
 Navicat Premium Dump SQL

 Source Server         : db_6
 Source Server Type    : SQLite
 Source Server Version : 3045000 (3.45.0)
 Source Schema         : main

 Target Server Type    : SQLite
 Target Server Version : 3045000 (3.45.0)
 File Encoding         : 65001

 Date: 16/07/2026 19:08:23
*/

PRAGMA foreign_keys = false;

-- ----------------------------
-- Table structure for _equipment_instances_old_20260401
-- ----------------------------
DROP TABLE IF EXISTS "_equipment_instances_old_20260401";
CREATE TABLE "_equipment_instances_old_20260401" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "equipment_type_id" VARCHAR(50) NOT NULL,
  "name" VARCHAR(200) NOT NULL,
  "status" VARCHAR(20) DEFAULT 'active',
  "created_time" text,
  "category" TEXT,
  "equipment_type_name" TEXT,
  FOREIGN KEY ("equipment_type_id") REFERENCES "equipment_types" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION,
  UNIQUE ("name" ASC)
);

-- ----------------------------
-- Table structure for documents
-- ----------------------------
DROP TABLE IF EXISTS "documents";
CREATE TABLE "documents" (
  "id" TEXT,
  "collection" TEXT NOT NULL,
  "doc" TEXT NOT NULL,
  "created_at" TEXT DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TEXT DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("id")
);

-- ----------------------------
-- Table structure for equipment_category
-- ----------------------------
DROP TABLE IF EXISTS "equipment_category";
CREATE TABLE "equipment_category" (
  "category_id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "category_name" VARCHAR(50) NOT NULL,
  "description" TEXT,
  UNIQUE ("category_name" ASC)
);

-- ----------------------------
-- Table structure for equipment_instances
-- ----------------------------
DROP TABLE IF EXISTS "equipment_instances";
CREATE TABLE "equipment_instances" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "equipment_type_id" VARCHAR(50) NOT NULL,
  "name" VARCHAR(200) NOT NULL,
  "status" VARCHAR(20) DEFAULT 'active',
  "created_time" text,
  "category" TEXT,
  "equipment_type_name" TEXT,
  UNIQUE ("name" ASC)
);

-- ----------------------------
-- Table structure for equipment_types
-- ----------------------------
DROP TABLE IF EXISTS "equipment_types";
CREATE TABLE "equipment_types" (
  "id" text NOT NULL,
  "name" text NOT NULL,
  "created_at" text,
  "updated_at" TEXT,
  "category" TEXT,
  PRIMARY KEY ("id")
);

-- ----------------------------
-- Table structure for graph_nodes
-- ----------------------------
DROP TABLE IF EXISTS "graph_nodes";
CREATE TABLE "graph_nodes" (
  "entity_type" TEXT NOT NULL,
  "entity_id" TEXT,
  "attributes" JSON NOT NULL,
  PRIMARY KEY ("entity_id")
);

-- ----------------------------
-- Table structure for graph_nodes_archive
-- ----------------------------
DROP TABLE IF EXISTS "graph_nodes_archive";
CREATE TABLE "graph_nodes_archive" (
  "entity_type" TEXT NOT NULL,
  "entity_id" TEXT,
  "attributes" JSON NOT NULL,
  PRIMARY KEY ("entity_id")
);

-- ----------------------------
-- Table structure for graph_relations
-- ----------------------------
DROP TABLE IF EXISTS "graph_relations";
CREATE TABLE "graph_relations" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "source_type" TEXT NOT NULL,
  "source_id" TEXT NOT NULL,
  "relation_type" TEXT NOT NULL,
  "target_type" TEXT NOT NULL,
  "target_id" TEXT NOT NULL
);

-- ----------------------------
-- Table structure for graph_relations_archive
-- ----------------------------
DROP TABLE IF EXISTS "graph_relations_archive";
CREATE TABLE "graph_relations_archive" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "source_type" TEXT NOT NULL,
  "source_id" TEXT NOT NULL,
  "relation_type" TEXT NOT NULL,
  "target_type" TEXT NOT NULL,
  "target_id" TEXT NOT NULL
);

-- ----------------------------
-- Table structure for maintenance_plans
-- ----------------------------
DROP TABLE IF EXISTS "maintenance_plans";
CREATE TABLE "maintenance_plans" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "plan_name" VARCHAR(200) NOT NULL,
  "plan_scale" VARCHAR(50),
  "status" VARCHAR(50) DEFAULT '待开始',
  "initiator" VARCHAR(100),
  "initiated_at" DATETIME,
  "planned_start_time" TEXT,
  "planned_end_time" TEXT,
  "actual_start_time" TEXT,
  "actual_end_time" TEXT,
  "planned_man_hours" REAL DEFAULT 0,
  "actual_man_hours" REAL DEFAULT 0,
  "planned_cost" REAL DEFAULT 0,
  "actual_cost" REAL DEFAULT 0,
  "schedule_plan_id" VARCHAR(100),
  "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------
-- Table structure for maintenance_tools
-- ----------------------------
DROP TABLE IF EXISTS "maintenance_tools";
CREATE TABLE "maintenance_tools" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "name" TEXT NOT NULL,
  "tool_type" TEXT NOT NULL,
  "capacity" REAL,
  "daily_rental_cost" REAL DEFAULT 0,
  "is_available" BOOLEAN DEFAULT 1,
  "requires_operator" BOOLEAN DEFAULT 0,
  "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------
-- Table structure for materials
-- ----------------------------
DROP TABLE IF EXISTS "materials";
CREATE TABLE "materials" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "name" TEXT NOT NULL,
  "price" REAL NOT NULL,
  "stock_quantity" REAL NOT NULL,
  "unit" TEXT NOT NULL,
  "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------
-- Table structure for process_templates
-- ----------------------------
DROP TABLE IF EXISTS "process_templates";
CREATE TABLE "process_templates" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "equipment_type_id" TEXT,
  "process_code" TEXT,
  "description" TEXT,
  "estimated_hours" REAL,
  "required_workers" TEXT,
  "predecessor_codes" TEXT,
  "parent_process_code" TEXT,
  "is_major_process" INTEGER,
  "material_requirements" TEXT,
  "tools_requirements" TEXT,
  "material_price" NUMBER,
  "tools_price" NUMBER,
  "worker_price" integer
);

-- ----------------------------
-- Table structure for schedule_tasks
-- ----------------------------
DROP TABLE IF EXISTS "schedule_tasks";
CREATE TABLE "schedule_tasks" (
  "schedule_id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "process_id" TEXT NOT NULL,
  "process_name" TEXT NOT NULL,
  "equipment_id" INTEGER NOT NULL,
  "equipment_name" TEXT NOT NULL,
  "equipment_type_id" TEXT,
  "equipment_type_name" TEXT,
  "equipment_category" TEXT,
  "start_time" INTEGER NOT NULL,
  "end_time" INTEGER NOT NULL,
  "start_time_formatted" TEXT NOT NULL,
  "end_time_formatted" TEXT NOT NULL,
  "duration_days" INTEGER NOT NULL,
  "workers" TEXT,
  "predecessors" TEXT
);

-- ----------------------------
-- Table structure for selected_equipments
-- ----------------------------
DROP TABLE IF EXISTS "selected_equipments";
CREATE TABLE "selected_equipments" (
  "id" INTEGER,
  "name" VARCHAR NOT NULL,
  "equipment_type_id" VARCHAR NOT NULL,
  "equipment_type_name" TEXT,
  "category" TEXT,
  "created_time" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("id")
);

-- ----------------------------
-- Table structure for selected_workers
-- ----------------------------
DROP TABLE IF EXISTS "selected_workers";
CREATE TABLE "selected_workers" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "worker_type_id" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "status" TEXT DEFAULT 0,
  "is_certified" INTEGER DEFAULT 0,
  "organization" TEXT,
  "emp_id" INTEGER,
  "compose" TEXT,
  "skill_level" integer,
  "phone" TEXT
);

-- ----------------------------
-- Table structure for sqlite_sequence
-- ----------------------------
DROP TABLE IF EXISTS "sqlite_sequence";
CREATE TABLE "sqlite_sequence" (
  "name",
  "seq"
);

-- ----------------------------
-- Table structure for task_operation_logs
-- ----------------------------
DROP TABLE IF EXISTS "task_operation_logs";
CREATE TABLE "task_operation_logs" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "task_id" INTEGER NOT NULL,
  "user_id" INTEGER,
  "operation_type" VARCHAR(50) NOT NULL,
  "description" TEXT,
  "attachment_path" VARCHAR(255),
  "old_status" VARCHAR(50),
  "new_status" VARCHAR(50),
  "approval_comments" TEXT,
  "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY ("task_id") REFERENCES "work_order_tasks" ("id") ON DELETE CASCADE ON UPDATE NO ACTION,
  FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE SET NULL ON UPDATE NO ACTION
);

-- ----------------------------
-- Table structure for uploaded_files
-- ----------------------------
DROP TABLE IF EXISTS "uploaded_files";
CREATE TABLE "uploaded_files" (
  "id" TEXT,
  "original_name" TEXT NOT NULL,
  "saved_path" TEXT NOT NULL,
  "category" TEXT NOT NULL,
  "upload_time" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- ----------------------------
-- Table structure for user_wx
-- ----------------------------
DROP TABLE IF EXISTS "user_wx";
CREATE TABLE "user_wx" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "wx_openid" TEXT NOT NULL,
  "user_id" INTEGER NOT NULL,
  "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "user_wx_users_id_fk" FOREIGN KEY ("user_id") REFERENCES "users" ("") ON DELETE NO ACTION ON UPDATE NO ACTION,
  UNIQUE ("wx_openid" ASC)
);

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS "users";
CREATE TABLE "users" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "username" VARCHAR(50) NOT NULL,
  "password" VARCHAR(200) NOT NULL,
  "email" VARCHAR(20),
  "role" VARCHAR(20) NOT NULL,
  "company_id" INTEGER,
  "real_name" VARCHAR(100),
  "phone" VARCHAR(20),
  "created_time" text,
  "emp_id" text
);

-- ----------------------------
-- Table structure for work_order_task_workers
-- ----------------------------
DROP TABLE IF EXISTS "work_order_task_workers";
CREATE TABLE "work_order_task_workers" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "task_id" INTEGER NOT NULL,
  "worker_id" INTEGER NOT NULL,
  "worker_name" VARCHAR(100) NOT NULL,
  "worker_type" VARCHAR(50),
  "status" VARCHAR(20) NOT NULL DEFAULT 'assigned',
  "completion_note" TEXT,
  "completed_at" DATETIME,
  "created_at" DATETIME DEFAULT (DATETIME('now', 'localtime')),
  FOREIGN KEY ("task_id") REFERENCES "work_order_tasks" ("id") ON DELETE CASCADE ON UPDATE NO ACTION,
  FOREIGN KEY ("worker_id") REFERENCES "workers" ("id") ON DELETE RESTRICT ON UPDATE NO ACTION
);

-- ----------------------------
-- Table structure for work_order_tasks
-- ----------------------------
DROP TABLE IF EXISTS "work_order_tasks";
CREATE TABLE "work_order_tasks" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "work_order_id" INTEGER NOT NULL,
  "task_code" VARCHAR(50),
  "process_id" VARCHAR(100) NOT NULL,
  "process_name" VARCHAR(200) NOT NULL,
  "equipment_id" INTEGER NOT NULL,
  "equipment_name" VARCHAR(100) NOT NULL,
  "description" TEXT,
  "estimated_hours" REAL,
  "scheduled_start_time" text,
  "scheduled_end_time" text,
  "actual_start_time" text,
  "actual_end_time" text,
  "status" VARCHAR(20) NOT NULL DEFAULT 'pending',
  "predecessor_task_ids" TEXT,
  "is_milestone" BOOLEAN NOT NULL DEFAULT 0,
  "workers" TEXT NOT NULL DEFAULT '[]',
  "approver_id" INTEGER,
  "approval_comments" TEXT,
  "approved_at" DATETIME,
  "created_at" DATETIME DEFAULT (DATETIME('now', 'localtime')),
  "updated_at" DATETIME DEFAULT (DATETIME('now', 'localtime')),
  "attachment_path" TEXT,
  "process_code" TEXT,
  FOREIGN KEY ("work_order_id") REFERENCES "work_orders" ("id") ON DELETE CASCADE ON UPDATE NO ACTION,
  FOREIGN KEY ("equipment_id") REFERENCES "_equipment_instances_old_20260401" ("id") ON DELETE RESTRICT ON UPDATE NO ACTION
);

-- ----------------------------
-- Table structure for work_orders
-- ----------------------------
DROP TABLE IF EXISTS "work_orders";
CREATE TABLE "work_orders" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "order_number" VARCHAR(50) NOT NULL,
  "title" VARCHAR(200) NOT NULL,
  "equipment_id" INTEGER NOT NULL,
  "equipment_name" VARCHAR(100) NOT NULL,
  "status" VARCHAR(20) NOT NULL DEFAULT 'pending',
  "created_by" INTEGER NOT NULL,
  "created_at" DATETIME DEFAULT (DATETIME('now', 'localtime')),
  "scheduled_start_time" INTEGER,
  "scheduled_end_time" INTEGER,
  "actual_start_time" INTEGER,
  "actual_end_time" INTEGER,
  "priority" VARCHAR(10) NOT NULL DEFAULT 'medium',
  "remarks" TEXT,
  "plan_id" INTEGER,
  FOREIGN KEY ("equipment_id") REFERENCES "_equipment_instances_old_20260401" ("id") ON DELETE RESTRICT ON UPDATE NO ACTION,
  FOREIGN KEY ("created_by") REFERENCES "users" ("id") ON DELETE RESTRICT ON UPDATE NO ACTION,
  UNIQUE ("order_number" ASC)
);

-- ----------------------------
-- Table structure for worker_team
-- ----------------------------
DROP TABLE IF EXISTS "worker_team";
CREATE TABLE "worker_team" (
  "workerteam_type" TEXT,
  "total" integer,
  "assigned" integer
);

-- ----------------------------
-- Table structure for worker_types
-- ----------------------------
DROP TABLE IF EXISTS "worker_types";
CREATE TABLE "worker_types" (
  "id" VARCHAR(50),
  "name" VARCHAR(50) NOT NULL,
  "description" TEXT,
  "requires_certification" BOOLEAN DEFAULT FALSE,
  "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  "price" integer,
  PRIMARY KEY ("id")
);

-- ----------------------------
-- Table structure for workers
-- ----------------------------
DROP TABLE IF EXISTS "workers";
CREATE TABLE "workers" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "worker_type_id" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "status" TEXT DEFAULT 0,
  "is_certified" INTEGER DEFAULT 0,
  "organization" TEXT,
  "emp_id" INTEGER,
  "compose" TEXT,
  "skill_level" integer,
  "phone" TEXT
);

-- ----------------------------
-- Auto increment value for _equipment_instances_old_20260401
-- ----------------------------
UPDATE "sqlite_sequence" SET seq = 50 WHERE name = '_equipment_instances_old_20260401';

-- ----------------------------
-- Auto increment value for equipment_category
-- ----------------------------
UPDATE "sqlite_sequence" SET seq = 13 WHERE name = 'equipment_category';

-- ----------------------------
-- Auto increment value for equipment_instances
-- ----------------------------
UPDATE "sqlite_sequence" SET seq = 56 WHERE name = 'equipment_instances';

-- ----------------------------
-- Auto increment value for graph_relations
-- ----------------------------
UPDATE "sqlite_sequence" SET seq = 40971 WHERE name = 'graph_relations';

-- ----------------------------
-- Indexes structure for table graph_relations
-- ----------------------------
CREATE UNIQUE INDEX "idx_relation_unique"
ON "graph_relations" (
  "source_id" ASC,
  "relation_type" ASC,
  "target_id" ASC
);

-- ----------------------------
-- Auto increment value for graph_relations_archive
-- ----------------------------
UPDATE "sqlite_sequence" SET seq = 40971 WHERE name = 'graph_relations_archive';

-- ----------------------------
-- Indexes structure for table graph_relations_archive
-- ----------------------------
CREATE UNIQUE INDEX "idx_relation_archive_unique"
ON "graph_relations_archive" (
  "source_id" ASC,
  "relation_type" ASC,
  "target_id" ASC
);

-- ----------------------------
-- Auto increment value for maintenance_tools
-- ----------------------------
UPDATE "sqlite_sequence" SET seq = 8 WHERE name = 'maintenance_tools';

-- ----------------------------
-- Auto increment value for materials
-- ----------------------------
UPDATE "sqlite_sequence" SET seq = 21 WHERE name = 'materials';

-- ----------------------------
-- Auto increment value for process_templates
-- ----------------------------
UPDATE "sqlite_sequence" SET seq = 116 WHERE name = 'process_templates';

-- ----------------------------
-- Auto increment value for schedule_tasks
-- ----------------------------
UPDATE "sqlite_sequence" SET seq = 4484 WHERE name = 'schedule_tasks';

-- ----------------------------
-- Auto increment value for selected_workers
-- ----------------------------
UPDATE "sqlite_sequence" SET seq = 46 WHERE name = 'selected_workers';

-- ----------------------------
-- Auto increment value for users
-- ----------------------------
UPDATE "sqlite_sequence" SET seq = 5 WHERE name = 'users';

-- ----------------------------
-- Auto increment value for work_order_task_workers
-- ----------------------------
UPDATE "sqlite_sequence" SET seq = 936 WHERE name = 'work_order_task_workers';

-- ----------------------------
-- Indexes structure for table work_order_task_workers
-- ----------------------------
CREATE INDEX "idx_wotw_status"
ON "work_order_task_workers" (
  "status" ASC
);
CREATE INDEX "idx_wotw_task_id"
ON "work_order_task_workers" (
  "task_id" ASC
);
CREATE INDEX "idx_wotw_worker_id"
ON "work_order_task_workers" (
  "worker_id" ASC
);

-- ----------------------------
-- Auto increment value for work_order_tasks
-- ----------------------------
UPDATE "sqlite_sequence" SET seq = 873 WHERE name = 'work_order_tasks';

-- ----------------------------
-- Auto increment value for work_orders
-- ----------------------------
UPDATE "sqlite_sequence" SET seq = 39 WHERE name = 'work_orders';

-- ----------------------------
-- Auto increment value for workers
-- ----------------------------
UPDATE "sqlite_sequence" SET seq = 46 WHERE name = 'workers';

PRAGMA foreign_keys = true;
