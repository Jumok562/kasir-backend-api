    const express = require('express');
    const { Pool } = require('pg'); // Menggunakan pg untuk PostgreSQL
    const cors = require('cors');

    const app = express();
    const PORT = process.env.PORT || 3000; // Port server

    // Inisialisasi Database PostgreSQL
    // PENTING: process.env.DATABASE_URL akan disediakan oleh Render saat di-deploy.
    // Anda TIDAK AKAN BISA menjalankan ini secara lokal di HP.
    const db = new Pool({
        connectionString: process.env.DATABASE_URL, // Ini akan diisi oleh Render
        ssl: {
            rejectUnauthorized: false // Penting untuk koneksi ke Render
        }
    });

    // Test koneksi database (akan berjalan saat di Render)
    db.connect((err, client, release) => {
        if (err) {
            return console.error('Error acquiring client', err.stack);
        }
        client.query('SELECT NOW()', (err, result) => {
            release(); // Lepaskan klien kembali ke pool
            if (err) {
                return console.error('Error executing query', err.stack);
            }
            console.log('Connected to PostgreSQL database at:', result.rows[0].now);
        });
    });

    // Buat tabel sales jika belum ada
    db.query(`
        CREATE TABLE IF NOT EXISTS sales (
            id SERIAL PRIMARY KEY,
            transactionId TEXT UNIQUE NOT NULL,
            timestamp TEXT NOT NULL,
            items TEXT NOT NULL,
            totalAmount REAL NOT NULL,
            paymentReceived REAL NOT NULL,
            changeAmount REAL NOT NULL,
            debtAmount REAL NOT NULL,
            status TEXT NOT NULL
        )
    `)
    .then(() => console.log('Sales table created or already exists.'))
    .catch(err => console.error('Error creating table:', err.message));


    // Middleware
    app.use(cors());
    app.use(express.json());

    // --- API Endpoints ---

    // 1. POST /sales - Menambahkan transaksi penjualan baru
    app.post('/sales', async (req, res) => {
        const { transactionId, timestamp, items, totalAmount, paymentReceived, change, debtAmount, status } = req.body;

        if (!transactionId || !timestamp || !items || totalAmount === undefined || paymentReceived === undefined || change === undefined || debtAmount === undefined || !status) {
            return res.status(400).json({ error: 'Missing required fields' });
        }

        const itemsJson = JSON.stringify(items);

        try {
            await db.query(
                `INSERT INTO sales (transactionId, timestamp, items, totalAmount, paymentReceived, changeAmount, debtAmount, status)
                 VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
                [transactionId, timestamp, itemsJson, totalAmount, paymentReceived, change, debtAmount, status]
            );
            res.status(201).json({ message: 'Sale added successfully' });
        } catch (err) {
            if (err.code === '23505') {
                return res.status(409).json({ error: 'Transaction ID already exists' });
            }
            console.error('Error inserting sale:', err.message);
            res.status(500).json({ error: 'Failed to add sale' });
        }
    });

    // 2. GET /sales - Mengambil semua riwayat penjualan
    app.get('/sales', async (req, res) => {
        try {
            const result = await db.query(`SELECT * FROM sales ORDER BY id DESC`);
            const parsedRows = result.rows.map(row => ({
                ...row,
                items: JSON.parse(row.items)
            }));
            res.status(200).json(parsedRows);
        } catch (err) {
            console.error('Error fetching sales:', err.message);
            res.status(500).json({ error: 'Failed to retrieve sales' });
        }
    });

    // 3. DELETE /sales/:transactionId - Menghapus transaksi berdasarkan transactionId
    app.delete('/sales/:transactionId', async (req, res) => {
        const transactionId = req.params.transactionId;
        try {
            const result = await db.query(`DELETE FROM sales WHERE transactionId = $1`, [transactionId]);
            if (result.rowCount === 0) {
                return res.status(404).json({ message: 'Transaction not found' });
            }
            res.status(200).json({ message: `Transaction ${transactionId} deleted successfully` });
        } catch (err) {
            console.error('Error deleting sale:', err.message);
            res.status(500).json({ error: 'Failed to delete sale' });
        }
    });

    // 4. DELETE /sales - Menghapus semua riwayat penjualan
    app.delete('/sales', async (req, res) => {
        try {
            const result = await db.query(`DELETE FROM sales`);
            res.status(200).json({ message: `All sales history deleted (${result.rowCount} rows affected)` });
        } catch (err) {
            console.error('Error deleting all sales:', err.message);
            res.status(500).json({ error: 'Failed to delete all sales' });
        }
    });

    // Mulai server (akan berjalan saat di Render)
    app.listen(PORT, () => {
        console.log(`Server is running on port ${PORT}`);
        console.log(`Access API at http://localhost:${PORT}`);
    });

    // Tutup koneksi DB saat aplikasi ditutup (tidak terlalu relevan untuk Render)
    process.on('SIGINT', async () => {
        await db.end();
        console.log('Database connection closed.');
        process.exit(0);
    });
    ```