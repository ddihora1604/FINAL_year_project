import { createTheme, alpha } from '@mui/material/styles';

const theme = createTheme({
    palette: {
        mode: 'dark',
        primary: {
            main: '#7b1fa2', // Violet
            light: '#ae52d4',
            dark: '#4a0072',
            contrastText: '#ffffff',
        },
        secondary: {
            main: '#2979ff', // Electric Blue
            light: '#75a7ff',
            dark: '#004ecb',
            contrastText: '#ffffff',
        },
        background: {
            default: '#0a1929', // Deep dark blue/gray
            paper: '#132f4c',   // Slightly lighter for cards/drawers
        },
        text: {
            primary: '#ffffff',
            secondary: alpha('#ffffff', 0.7),
        },
        success: {
            main: '#00e676',
        },
        warning: {
            main: '#ffea00',
        },
        error: {
            main: '#ff1744',
        },
    },
    typography: {
        fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
        h1: { fontWeight: 700 },
        h2: { fontWeight: 700 },
        h3: { fontWeight: 600 },
        h4: { fontWeight: 600 },
        h5: { fontWeight: 600 },
        h6: { fontWeight: 600 },
    },
    components: {
        MuiCssBaseline: {
            styleOverrides: {
                body: {
                    scrollbarColor: '#6b6b6b #2b2b2b',
                    '&::-webkit-scrollbar, & *::-webkit-scrollbar': {
                        backgroundColor: '#2b2b2b',
                        width: '8px',
                        height: '8px',
                    },
                    '&::-webkit-scrollbar-thumb, & *::-webkit-scrollbar-thumb': {
                        borderRadius: 8,
                        backgroundColor: '#6b6b6b',
                        minHeight: 24,
                        border: '2px solid #2b2b2b',
                    },
                    '&::-webkit-scrollbar-thumb:focus, & *::-webkit-scrollbar-thumb:focus': {
                        backgroundColor: '#959595',
                    },
                    '&::-webkit-scrollbar-thumb:active, & *::-webkit-scrollbar-thumb:active': {
                        backgroundColor: '#959595',
                    },
                    '&::-webkit-scrollbar-thumb:hover, & *::-webkit-scrollbar-thumb:hover': {
                        backgroundColor: '#959595',
                    },
                },
            },
        },
        MuiPaper: {
            styleOverrides: {
                root: {
                    backgroundImage: 'none',
                    '&.MuiPaper-elevation1': {
                        boxShadow: '0px 2px 4px -1px rgba(0,0,0,0.2), 0px 4px 5px 0px rgba(0,0,0,0.14), 0px 1px 10px 0px rgba(0,0,0,0.12)',
                    },
                },
            },
        },
        MuiButton: {
            styleOverrides: {
                root: {
                    textTransform: 'none',
                    borderRadius: 8,
                    fontWeight: 600,
                },
                containedPrimary: {
                    background: 'linear-gradient(45deg, #7b1fa2 30%, #2979ff 90%)',
                    boxShadow: '0 3px 5px 2px rgba(123, 31, 162, .3)',
                },
            },
        },
        MuiAppBar: {
            styleOverrides: {
                root: {
                    background: alpha('#0a1929', 0.8),
                    backdropFilter: 'blur(8px)',
                    boxShadow: 'none',
                    borderBottom: '1px solid rgba(255, 255, 255, 0.12)',
                },
            },
        },
        MuiDrawer: {
            styleOverrides: {
                paper: {
                    backgroundColor: '#0a1929',
                    borderRight: '1px solid rgba(255, 255, 255, 0.12)',
                },
            },
        },
    },
});

export default theme;
