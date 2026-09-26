/*
SQLyog Community v13.1.5  (64 bit)
MySQL - 8.1.0 : Database - studysync
*********************************************************************
*/

/*!40101 SET NAMES utf8 */;

/*!40101 SET SQL_MODE=''*/;

/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
CREATE DATABASE /*!32312 IF NOT EXISTS*/`studysync` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `studysync`;

/*Table structure for table `allowances` */

DROP TABLE IF EXISTS `allowances`;

CREATE TABLE `allowances` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `week_start` date NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `allowances_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Data for the table `allowances` */

/*Table structure for table `class_schedules` */

DROP TABLE IF EXISTS `class_schedules`;

CREATE TABLE `class_schedules` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `subject_id` int NOT NULL,
  `day` varchar(20) NOT NULL,
  `start_time` time NOT NULL,
  `end_time` time NOT NULL,
  `room` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `subject_id` (`subject_id`),
  CONSTRAINT `class_schedules_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `class_schedules_ibfk_2` FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Data for the table `class_schedules` */

/*Table structure for table `documents` */

DROP TABLE IF EXISTS `documents`;

CREATE TABLE `documents` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `filename` varchar(255) NOT NULL,
  `filepath` varchar(500) NOT NULL,
  `uploaded_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `documents_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Data for the table `documents` */

/*Table structure for table `expenses` */

DROP TABLE IF EXISTS `expenses`;

CREATE TABLE `expenses` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `allowance_id` int DEFAULT NULL,
  `description` varchar(255) NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `expense_date` date NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `allowance_id` (`allowance_id`),
  CONSTRAINT `expenses_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `expenses_ibfk_2` FOREIGN KEY (`allowance_id`) REFERENCES `allowances` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Data for the table `expenses` */

/*Table structure for table `flashcard_decks` */

DROP TABLE IF EXISTS `flashcard_decks`;

CREATE TABLE `flashcard_decks` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `title` varchar(255) NOT NULL,
  `subject` varchar(150) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `flashcard_decks_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Data for the table `flashcard_decks` */

/*Table structure for table `flashcards` */

DROP TABLE IF EXISTS `flashcards`;

CREATE TABLE `flashcards` (
  `id` int NOT NULL AUTO_INCREMENT,
  `deck_id` int NOT NULL,
  `question` text NOT NULL,
  `answer` text NOT NULL,
  PRIMARY KEY (`id`),
  KEY `deck_id` (`deck_id`),
  CONSTRAINT `flashcards_ibfk_1` FOREIGN KEY (`deck_id`) REFERENCES `flashcard_decks` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Data for the table `flashcards` */

/*Table structure for table `notes` */

DROP TABLE IF EXISTS `notes`;

CREATE TABLE `notes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `title` varchar(255) NOT NULL,
  `content` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `notes_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Data for the table `notes` */

/*Table structure for table `quiz_results` */

DROP TABLE IF EXISTS `quiz_results`;

CREATE TABLE `quiz_results` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `deck_id` int NOT NULL,
  `score` int NOT NULL,
  `total_items` int NOT NULL,
  `taken_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `deck_id` (`deck_id`),
  CONSTRAINT `quiz_results_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `quiz_results_ibfk_2` FOREIGN KEY (`deck_id`) REFERENCES `flashcard_decks` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Data for the table `quiz_results` */

/*Table structure for table `subjects` */

DROP TABLE IF EXISTS `subjects`;

CREATE TABLE `subjects` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `subjects_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Data for the table `subjects` */

/*Table structure for table `tasks` */

DROP TABLE IF EXISTS `tasks`;

CREATE TABLE `tasks` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `title` varchar(255) NOT NULL,
  `description` text,
  `due_date` date DEFAULT NULL,
  `priority` varchar(20) DEFAULT 'Medium',
  `completed` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `tasks_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Data for the table `tasks` */

/*Table structure for table `users` */

DROP TABLE IF EXISTS `users`;

CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(100) NOT NULL,
  `email` varchar(150) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Data for the table `users` */

insert  into `users`(`id`,`username`,`email`,`password_hash`,`created_at`) values 
(1,'feuna','feunacrizethlagolos@gmail.com','scrypt:32768:8:1$Fd56S190BC36ReRH$7ee1ad2dfda8eb234d81d114eb766273eb93efa39b5ad5d24ba665d0af959517b167a79f87d415c9777d6cd5411086a65e43b6f27bad03edd958266e59fe387b','2026-09-17 12:28:56'),
(2,'carlo','humangitjohncarlo3209214818718200608@gmail.com','scrypt:32768:8:1$MH1opB3bfYc7NB9Q$ecbab85a8743eabf98003f0e1a552afc77b3b7361c1aa5420ae357ba85b91ba4e568fe2c5bf8d4a707587e0cab326b61c575efec9b28e9fee946bff229ed702f','2026-09-17 12:34:31'),
(3,'ibon','yvonneonly556@gmail.com','scrypt:32768:8:1$iNDrXmkTGOrueC5b$89c91f3dbc6af725aa227144131a9d485bd3b63765db0b39245041af3accb0d124cae6497d74b0894f88cf9b0c2bf8954d6175823bb26f4a115ee23620cd8c08','2026-09-17 13:21:06'),
(4,'jullia','dediosjullia2006@gmail.com','scrypt:32768:8:1$SJdgwtIcWbCbt017$02f1e9a685423f19aa4d20a67787acca1f0b57f99b8f04562f509dcfc6ca3dd970e2e4219577b9c02b127d1368ee32810abe6522eb2438a5e79b8b601bdd450c','2026-09-17 18:40:10'),
(5,'fdsds','sdsdqawdasfcasfcas@gmail.com','scrypt:32768:8:1$la6LeMbIzDU5W2aP$e9058a0afbdec09a28644f9f949f24c0be7d2c9747bc29699c05cdcc9f324a9aa2882190ed4b0edf4aa2ee73eb56585687e914a916fbc96e645d4a7c613b880f','2026-09-17 18:45:44');

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;


--------- here ko ni sumpay 

USE studysync;
ALTER TABLE users ADD COLUMN is_verified BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE expenses ADD COLUMN category VARCHAR(50) DEFAULT 'Other';

describe users;
describe expenses;

SELECT * FROM users WHERE username = 'dedios';
SELECT * FROM tasks WHERE user_id = (SELECT id FROM users WHERE username = 'dedios');

