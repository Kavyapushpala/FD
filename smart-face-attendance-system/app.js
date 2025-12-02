const express = require('express');
const axios = require('axios');
const cors = require('cors');
const FormData = require('form-data');
const multer = require('multer');

const app = express();
const upload = multer();
const PORT = 3000;
const FLASK_URL = 'http://127.0.0.1:5000';

app.use(cors());
app.use(express.static('public')); // This serves your HTML, CSS, and JS files from a 'public' folder

// Proxy endpoint for offline attendance check-in
app.post('/api/mark_in', upload.single('image'), async (req, res) => {
    if (!req.file) {
        return res.status(400).json({ message: "No image file provided." });
    }
    const form = new FormData();
    form.append('image', req.file.buffer, { filename: req.file.originalname, contentType: req.file.mimetype });

    try {
        const flaskResponse = await axios.post(`${FLASK_URL}/mark_in`, form, {
            headers: form.getHeaders(),
        });
        res.json(flaskResponse.data);
    } catch (error) {
        res.status(500).json({ message: "Error communicating with Flask server." });
    }
});

// Proxy endpoint for offline attendance check-out
app.post('/api/mark_out', upload.single('image'), async (req, res) => {
    if (!req.file) {
        return res.status(400).json({ message: "No image file provided." });
    }
    const form = new FormData();
    form.append('image', req.file.buffer, { filename: req.file.originalname, contentType: req.file.mimetype });

    try {
        const flaskResponse = await axios.post(`${FLASK_URL}/mark_out`, form, {
            headers: form.getHeaders(),
        });
        res.json(flaskResponse.data);
    } catch (error) {
        res.status(500).json({ message: "Error communicating with Flask server." });
    }
});

// Proxy endpoint for online attendance verification
app.post('/api/mark_online', upload.single('image'), async (req, res) => {
    if (!req.file || !req.body.reg_no) {
        return res.status(400).json({ message: "Missing image or registration number." });
    }
    const form = new FormData();
    form.append('image', req.file.buffer, { filename: req.file.originalname, contentType: req.file.mimetype });
    form.append('reg_no', req.body.reg_no);

    try {
        const flaskResponse = await axios.post(`${FLASK_URL}/mark_online`, form, {
            headers: form.getHeaders(),
        });
        res.json(flaskResponse.data);
    } catch (error) {
        res.status(500).json({ message: "Error communicating with Flask server." });
    }
});

// Proxy endpoint to get attendance history
app.get('/api/get_history/:reg_no', async (req, res) => {
    try {
        const flaskResponse = await axios.get(`${FLASK_URL}/get_history/${req.params.reg_no}`);
        res.json(flaskResponse.data);
    } catch (error) {
        res.status(500).json({ message: "Error communicating with Flask server." });
    }
});

app.listen(PORT, () => {
    console.log(`Express.js server listening on port ${PORT}`);
});