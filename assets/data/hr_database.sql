-- Query the HR database

-- Sample queries for hr_database.sqlite

-- Get all employees with their department and job information
SELECT p.first_name, p.last_name, d.department_name, j.job_title
FROM per p
JOIN dept d ON p.department_id = d.department_id
JOIN jobs j ON p.job_id = j.job_id;

-- Get department-wise salary statistics
SELECT d.department_name,
       COUNT(*) as employee_count,
       ROUND(AVG(p.salary), 2) as avg_salary,
       MIN(p.salary) as min_salary,
       MAX(p.salary) as max_salary
FROM per p
JOIN dept d ON p.department_id = d.department_id
GROUP BY d.department_name;

-- Get employees who have changed jobs (job history)
SELECT p.first_name, p.last_name, 
       j1.job_title as old_job,
       j2.job_title as current_job,
       jh.start_date, jh.end_date
FROM per p
JOIN job_history jh ON p.employee_id = jh.employee_id
JOIN jobs j1 ON jh.job_id = j1.job_id
JOIN jobs j2 ON p.job_id = j2.job_id;

-- Get employees with their managers
SELECT e.first_name || ' ' || e.last_name as employee_name,
       m.first_name || ' ' || m.last_name as manager_name
FROM per e
LEFT JOIN per m ON e.manager_id = m.id;

-- Get department locations
SELECT d.department_name,
       l.city,
       l.state_province,
       l.country_id
FROM dept d
JOIN locations l ON d.location_id = l.location_id;

-- Get salary statistics by job title
SELECT j.job_title,
       COUNT(*) as employee_count,
       ROUND(AVG(p.salary), 2) as avg_salary,
       MIN(p.salary) as min_salary,
       MAX(p.salary) as max_salary
FROM per p
JOIN jobs j ON p.job_id = j.job_id
GROUP BY j.job_title;

-- Get employees hired in the last year
SELECT first_name, last_name, hire_date
FROM per
WHERE hire_date >= date('now', '-1 year')
ORDER BY hire_date DESC;

-- Get departments with more than 5 employees
SELECT d.department_name, COUNT(*) as employee_count
FROM dept d
JOIN per p ON d.department_id = p.department_id
GROUP BY d.department_name
HAVING COUNT(*) > 5;

-- Get employees with commission
SELECT first_name, last_name, salary, commission_pct,
       ROUND(salary * (1 + commission_pct), 2) as total_compensation
FROM per
WHERE commission_pct IS NOT NULL
ORDER BY total_compensation DESC;

-- Get job history duration for each employee
SELECT p.first_name, p.last_name,

       jh.job_id,
       julianday(jh.end_date) - julianday(jh.start_date) as days_in_role
FROM per p
JOIN job_history jh ON p.employee_id = jh.employee_id
ORDER BY days_in_role DESC;

