export function createApiClient(onUnauthorized) {
    return async function requestJson(path, method = 'GET', data) {
        let response;
        try {
            response = await fetch('/api' + path, {
                method,
                headers: method === 'GET' ? {} : {
                    'Content-Type': 'application/json',
                    'X-RotaClara': '1'
                },
                body: data === undefined ? undefined : JSON.stringify(data)
            });
        } catch {
            throw new Error('Não foi possível conectar ao servidor. Tente novamente.');
        }
        const result = await response.json();
        if (!response.ok) {
            if (response.status === 401 && path !== '/login') onUnauthorized();
            throw new Error(result.erro || 'Não foi possível concluir.');
        }
        return result;
    };
}
